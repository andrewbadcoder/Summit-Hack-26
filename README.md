# Summit-Hack-26

Spotware is a hardware sustainability assistant.

Given an image of a hardware component (uploaded image or webcam capture), the app:
1. Identifies the component using a vision model.
2. Converts that identification into structured JSON.
3. Looks up sustainability impact and disposal/recovery guidance.
4. Displays a clear action recommendation (reuse, refurbish, recycle, manual review).

## How The Program Works

- `Spotware/app.py`
  - Streamlit frontend.
  - Handles file upload/camera input.
  - Calls perception + sustainability modules.
  - Renders results cards and raw JSON.

- `perception.py`
  - Vision layer (Gemini API).
  - Input: image bytes or file path.
  - Output: normalized JSON (`device_class`, `condition`, `confidence`, etc.).

- `sustainability.py`
  - Decision-support lookup layer over `sustainability_data.json`.
  - Normalizes names (aliases like `graphics_card` -> `gpu`).
  - Returns impact metrics and default action fallback (`undetected` for unknowns).

- `sustainability_data.json`
  - Component-level embodied CO2, recoverable metals, refurb/scrap value, hazard flags, source tags.

## Project Structure

```text
Summit-Hack-26/
  Spotware/
    app.py
    logo1.png
  perception.py
  sustainability.py
  sustainability_data.json
  sources.md
  requirements.txt
```

## Prerequisites

- Python 3.10+ (3.11/3.12 recommended)
- A Gemini API key

## Setup

1. Open a terminal in the repo root:

```powershell
cd "c:\Users\james\OneDrive\Desktop\COMP\CurrentClasses\Sandbox\SummerHack2025\Summit-Hack-26"
```

2. (Recommended) Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in the repo root (`Summit-Hack-26/.env`) with one of:

```env
GEMINI_API_KEY=your_real_key_here
# or
GOOGLE_API_KEY=your_real_key_here

# optional
GEMINI_MODEL=gemini-2.5-flash
```

## Run Locally (Host The App)

From repo root:

```powershell
streamlit run Spotware/app.py
```

Streamlit will print a local URL (typically `http://localhost:8501`).
Open that URL in your browser.

## Using The App

1. Upload an image or take a photo with webcam capture.
2. Click `Run analysis`.
3. Review:
   - Identification (device class, manufacturer, model, confidence)
   - Sustainability snapshot (embodied CO2, scrap/refurb value, hazard flags)
   - Suggested action

## Optional: Batch Test Perception Only

Run perception over a folder of images:

```powershell
python perception.py images\gpu --print
```

Outputs JSON files under `<folder>\out` by default.

## Troubleshooting

- `Set GEMINI_API_KEY or GOOGLE_API_KEY...`
  - `.env` is missing, misplaced, or key is invalid.
  - Ensure `.env` is in repo root, next to `perception.py`.

- `ModuleNotFoundError`
  - Re-activate your venv and re-run `pip install -r requirements.txt`.

- Streamlit command not found
  - Use `python -m streamlit run Spotware/app.py`.

- Unknown component returned
  - Perception may output a class not in the lookup table; `sustainability.py` safely falls back to `undetected`.

