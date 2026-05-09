"""
Hardware image perception via Gemini VLM: one image in, structured JSON out.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types

ImageInput = Union[str, Path, bytes]

REQUIRED_KEYS = frozenset(
    {
        "device_class",
        "manufacturer",
        "model",
        "visible_text",
        "condition",
        "form_factor",
        "generation_hint",
        "data_bearing",
        "contains_hazardous",
        "completeness",
        "confidence",
        "notes",
    }
)

DEFAULT_MODEL = "gemini-2.5-flash"
_IMAGE_SUFFIX_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def load_gemini_api_key() -> str:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key or key == "your_key_here":
        key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key or key == "your_key_here":
        raise RuntimeError(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in .env (see .env.example). "
            "Get a key at https://aistudio.google.com/apikey"
        )
    return key


def _sniff_mime(image_bytes: bytes) -> str | None:
    if len(image_bytes) >= 3 and image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(image_bytes) >= 8 and image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(image_bytes) >= 12 and image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if len(image_bytes) >= 6 and image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return None


def _load_image_bytes_and_mime(image: ImageInput) -> tuple[bytes, str]:
    if isinstance(image, bytes):
        mime = _sniff_mime(image)
        if not mime:
            raise ValueError(
                "Could not detect image type from bytes; pass a file path or use a standard JPEG/PNG/WebP/GIF."
            )
        return image, mime

    path = Path(image)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    suffix = path.suffix.lower()
    mime = _IMAGE_SUFFIX_TO_MIME.get(suffix)
    data = path.read_bytes()
    if not mime:
        mime = _sniff_mime(data)
    if not mime:
        raise ValueError(f"Unsupported image type for {path}")
    return data, mime


def _build_prompt() -> str:
    return """You are a hardware perception model for e-waste / recycling triage.
Look at the photo and fill a single JSON object. Rules:
- Output ONLY valid JSON. No markdown, no code fences, no commentary before or after.
- Use EXACTLY these keys (all required): device_class, manufacturer, model, visible_text, condition, form_factor, generation_hint, data_bearing, contains_hazardous, completeness, confidence, notes
- visible_text: array of strings for text you can actually read in the image. Do not invent model numbers or labels not visible; use fewer entries if unsure.
- condition: one of good, fair, poor, unknown
- generation_hint: one of modern, legacy, unknown
- completeness: one of complete, partial, unknown, missing_minor_parts, missing_major_parts
- data_bearing: true if the item likely stores user data (e.g. SSD, HDD, phone, tablet, laptop with storage visible)
- contains_hazardous: true if it is or likely contains hazardous e-waste (e.g. lithium battery cells, CRT, mercury bulbs). Use false when clearly not; unknown cases use best judgment and lower confidence.
- confidence: number from 0.0 to 1.0 for how sure you are about device_class/manufacturer/model overall
- manufacturer / model: use "Unknown" if not readable
- notes: short factual observations only (form factor cues, visible damage, slot type, etc.)

Example shape (values illustrative):
{"device_class":"GPU","manufacturer":"NVIDIA","model":"A100","visible_text":["NVIDIA","A100","80GB"],"condition":"good","form_factor":"PCIe","generation_hint":"modern","data_bearing":true,"contains_hazardous":false,"completeness":"complete","confidence":0.92,"notes":"PCIe card, no visible damage"}"""


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", t, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\n---\n{cleaned[:2000]}") from e


def _validate_and_coerce(raw: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_KEYS - raw.keys()
    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    out: dict[str, Any] = {}
    for k in sorted(REQUIRED_KEYS):
        out[k] = raw[k]

    if not isinstance(out["visible_text"], list):
        raise ValueError("visible_text must be a JSON array")
    out["visible_text"] = [str(x) for x in out["visible_text"]]

    for key in (
        "device_class",
        "manufacturer",
        "model",
        "condition",
        "form_factor",
        "generation_hint",
        "completeness",
        "notes",
    ):
        if not isinstance(out[key], str):
            out[key] = str(out[key])

    for key in ("data_bearing", "contains_hazardous"):
        if isinstance(out[key], str):
            low = out[key].lower()
            out[key] = low in ("true", "1", "yes")
        else:
            out[key] = bool(out[key])

    c = out["confidence"]
    if isinstance(c, str):
        try:
            c = float(c)
        except ValueError as e:
            raise ValueError("confidence must be a number") from e
    elif not isinstance(c, (int, float)):
        raise ValueError("confidence must be a number")
    out["confidence"] = max(0.0, min(1.0, float(c)))

    return out


def _call_gemini_vision(
    image_bytes: bytes,
    mime_type: str,
    *,
    api_key: str,
    model: str,
) -> str:
    client = genai.Client(api_key=api_key)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    prompt = _build_prompt()
    response = client.models.generate_content(
        model=model,
        contents=[image_part, prompt],
    )
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Empty response from Gemini (no text).")
    return text


def perceive(image: ImageInput, *, model: str | None = None) -> dict[str, Any]:
    """
    Analyze a hardware photo and return the perception JSON dict.

    ``image`` may be a filesystem path (str or Path) or raw image bytes.
    Set GEMINI_API_KEY in the environment or .env. Optional GEMINI_MODEL overrides the default.
    """
    api_key = load_gemini_api_key()
    resolved_model = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL).strip()
    image_bytes, mime_type = _load_image_bytes_and_mime(image)
    raw_text = _call_gemini_vision(
        image_bytes,
        mime_type,
        api_key=api_key,
        model=resolved_model,
    )
    parsed = _parse_json_response(raw_text)
    return _validate_and_coerce(parsed)


_FOLLOWUP_SYSTEM_PREFIX = """You are an e-waste triage and sustainability advisor.
Ground answers in the perception and sustainability JSON in your instructions.
If the user asks for something not supported by that JSON, say so and give only general best-practice guidance—do not invent specific facilities, prices, laws, or certifications.
Prioritize safety, data-bearing devices, and hazardous materials. Be concise unless the user asks for detail.

--- ANALYSIS CONTEXT (JSON) ---
"""


def followup_answer(
    *,
    user_message: str,
    perception: dict[str, Any],
    sustainability: dict[str, Any],
    history: list[tuple[str, str]],
    model: str | None = None,
) -> str:
    """
    Answer a follow-up question using the same Gemini model, with perception + sustainability
    as fixed context. ``history`` is prior (user text, assistant text) pairs in order.
    """
    text = user_message.strip()
    if not text:
        raise ValueError("Follow-up message must not be empty.")

    api_key = load_gemini_api_key()
    resolved_model = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL).strip()
    context_json = json.dumps(
        {"perception": perception, "sustainability": sustainability},
        indent=2,
    )
    sys_text = _FOLLOWUP_SYSTEM_PREFIX + context_json

    contents: list[types.Content] = []
    for user_txt, model_txt in history:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_txt)],
            )
        )
        contents.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text=model_txt)],
            )
        )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        )
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=resolved_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=types.Content(
                role="user",
                parts=[types.Part.from_text(text=sys_text)],
            ),
        ),
    )
    out = (response.text or "").strip()
    if not out:
        raise RuntimeError("Empty response from Gemini (follow-up).")
    return out


def _iter_images(folder: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    files = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts
    )
    return files


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Run perception on all images in a folder; write JSON alongside or under out/"
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Directory containing images (.jpg, .png, .webp, .gif)",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=None,
        help="Write <stem>.json here (default: <folder>/out)",
    )
    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="Print each result JSON to stdout",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="Gemini model id (default: env GEMINI_MODEL or gemini-2.0-flash)",
    )
    args = parser.parse_args()

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        raise SystemExit(f"Not a directory: {folder}")

    out_dir = (args.out_dir or (folder / "out")).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    images = _iter_images(folder)
    if not images:
        raise SystemExit(f"No images found in {folder}")

    failures: list[tuple[Path, str]] = []
    for path in images:
        try:
            result = perceive(path, model=args.model)
            text = json.dumps(result, indent=2)
            if args.print:
                print(f"=== {path.name} ===\n{text}\n")
            out_path = out_dir / f"{path.stem}.json"
            out_path.write_text(text + "\n", encoding="utf-8")
        except Exception as e:
            msg = str(e)
            failures.append((path, msg))
            snippet = msg[:500]
            print(f"[FAIL] {path.name}: {snippet}", file=sys.stderr)

    if failures:
        print(f"\nDone with {len(failures)} failure(s) out of {len(images)}.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Wrote {len(images)} JSON file(s) to {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    _main()
