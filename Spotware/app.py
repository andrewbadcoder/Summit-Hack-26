import json
import sys
from pathlib import Path

import streamlit as st

# Repo root (parent of Spotware/) so `perception` and `sustainability` resolve
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from perception import followup_answer, perceive  # noqa: E402
from sustainability import get_sustainability_record  # noqa: E402
from decision import recommend_action  # noqa: E402

# ── MUST be first Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="Spotware",
    page_icon="logo1.png",
    layout="centered",
)


# ── Fonts + Title Styling ────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700;800;900&display=swap');

        html, body, [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stMarkdown"] {
            font-family: 'Inter', sans-serif !important;
        }

        .hero-title {
            font-family: 'DM Sans', sans-serif;
            font-size: clamp(7rem, 20vw, 30rem);
            font-weight: 900;
            text-align: center;
            letter-spacing: -0.03em;
            line-height: 1;
            width: 100%;
            padding: 2rem 0 0.5rem 0;
            color: inherit;
        }

        .hero-divider {
            border: none;
            border-top: 1px solid rgba(128,128,128,0.2);
            margin: 0 auto 3rem auto;   /* ← increased bottom margin */
            width: 80%;
        }

/* ── Extra breathing room before the upload widgets ── */
        .block-container {
            padding-top: 1rem !important;
        }

        .hero-subtitle {
            
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 400;
            text-align: center;
            opacity: 0.6;
            margin-bottom: 3rem;        /* ← increased from 2.5rem */
        }
    </style>
""",
    unsafe_allow_html=True,
)

_LOGO = Path(__file__).resolve().parent / "logo1.png"
if _LOGO.is_file():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(str(_LOGO), use_container_width=True)

st.markdown("<h1 class='hero-title'>Spotware</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='hero-subtitle'>Upload or capture a photo of hardware for perception + sustainability lookup.</p>",
    unsafe_allow_html=True,
)
st.markdown("<hr class='hero-divider'>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
picture = st.camera_input("Take a picture")

image_bytes: bytes | None = None
mime_hint: str | None = None
source_label = ""

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    mime_hint = uploaded_file.type or None
    source_label = uploaded_file.name
    st.image(uploaded_file, caption="Uploaded image", use_container_width=True)
elif picture is not None:
    image_bytes = picture.getvalue()
    mime_hint = picture.type or None
    source_label = "camera"
    st.image(picture, caption="Camera capture", use_container_width=True)

if "last_perception" not in st.session_state:
    st.session_state.last_perception = None
if "last_sustainability" not in st.session_state:
    st.session_state.last_sustainability = None
if "last_decision" not in st.session_state:
    st.session_state.last_decision = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "followup_messages" not in st.session_state:
    st.session_state.followup_messages = []

if image_bytes:
    run = st.button("Run analysis", type="primary")
    if run:
        st.session_state.last_error = None
        st.session_state.last_perception = None
        st.session_state.last_sustainability = None
        st.session_state.last_decision = None
        st.session_state.followup_messages = []
        with st.spinner("Calling Gemini vision…"):
            try:
                perception = perceive(image_bytes)
                sustainability = get_sustainability_record(
                    perception.get("device_class")
                )
                decision = recommend_action(perception, sustainability)
                st.session_state.last_perception = perception
                st.session_state.last_sustainability = sustainability
                st.session_state.last_decision = decision
            except Exception as e:
                st.session_state.last_error = str(e)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    per = st.session_state.last_perception
    sus = st.session_state.last_sustainability
    dec = st.session_state.last_decision
    if per is not None and sus is not None and dec is not None:
        st.subheader("Identification")
        c1, c2, c3 = st.columns(3)
        c1.metric("Device class", per.get("device_class", "—"))
        c2.metric("Manufacturer", per.get("manufacturer", "—"))
        c3.metric("Model", per.get("model", "—"))
        st.caption(
            f"Condition: **{per.get('condition', '—')}** · "
            f"Completeness: **{per.get('completeness', '—')}** · "
            f"Confidence: **{per.get('confidence', 0):.0%}**"
        )
        if per.get("notes"):
            st.info(per["notes"])

        # ── Recommended action (the headline) ─────────────────────────────────
        st.subheader("Recommended action")
        _ACTION_COLORS = {
            "green": ("#EAF3DE", "#173404", "#3B6D11", "#639922"),
            "blue":  ("#E6F1FB", "#042C53", "#185FA5", "#378ADD"),
            "amber": ("#FAEEDA", "#412402", "#854F0B", "#BA7517"),
            "red":   ("#FCEBEB", "#501313", "#A32D2D", "#E24B4A"),
        }
        bg, fg, sub, border = _ACTION_COLORS.get(
            dec.get("color", "amber"), _ACTION_COLORS["amber"]
        )
        st.markdown(
            f"""
            <div style='background:{bg};border-left:4px solid {border};
                        padding:14px 18px;border-radius:8px;margin:8px 0 16px 0'>
              <div style='font-size:11px;color:{sub};text-transform:uppercase;
                          letter-spacing:0.5px;font-weight:500'>
                Action
              </div>
              <div style='font-size:20px;font-weight:600;color:{fg};margin-top:2px'>
                {dec.get("label", "—")}
              </div>
              <div style='font-size:14px;color:{sub};margin-top:6px;line-height:1.5'>
                {dec.get("reason", "")}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Sustainability impact ─────────────────────────────────────────────
        st.subheader("Sustainability impact")
        m1, m2, m3 = st.columns(3)
        m1.metric("CO₂ avoided", f"{dec.get('co2_avoided_kg', 0)} kg")
        m2.metric("Recovery value", f"${dec.get('value_usd', 0)}")
        m3.metric("Recoverable metals", f"{dec.get('metals_total_g', 0):.0f} g")
        if dec.get("source"):
            st.caption(f"📚 Source: {dec['source']}")

        metals = dec.get("metals_breakdown_g") or sus.get("recoverable_metals_g")
        if isinstance(metals, dict) and metals:
            with st.expander("Metal breakdown"):
                st.json(metals)

        flags = sus.get("hazard_flags")
        if isinstance(flags, list) and flags:
            st.warning("Hazard flags: " + ", ".join(str(x) for x in flags))

        # ── Why this recommendation? (rule trace) ─────────────────────────────
        with st.expander("Why this recommendation?"):
            st.markdown("**Decision logic trace**")
            for step in dec.get("rule_trace", []):
                st.markdown(f"- {step}")
            st.markdown(
                f"\n**Final action:** `{dec.get('action', '—')}`"
            )

        with st.expander("Raw perception JSON"):
            st.code(json.dumps(per, indent=2), language="json")
        with st.expander("Raw sustainability record"):
            st.code(json.dumps(sus, indent=2), language="json")
        with st.expander("Raw decision output"):
            st.code(json.dumps(dec, indent=2), language="json")

        st.subheader("Follow-up questions")
        st.caption(
            "Ask about risks, data destruction, recycling paths, or repair—the model uses "
            "your analysis above as context."
        )
        for msg in st.session_state.followup_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input(
            "e.g. Is it safe to store this in a closet? Where should I take it?"
        ):
            history: list[tuple[str, str]] = []
            msgs = st.session_state.followup_messages
            i = 0
            while i + 1 < len(msgs):
                if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
                    history.append((msgs[i]["content"], msgs[i + 1]["content"]))
                i += 2
            try:
                with st.spinner("Asking Gemini…"):
                    reply = followup_answer(
                        user_message=prompt,
                        perception=per,
                        sustainability=sus,
                        history=history,
                    )
            except Exception as e:
                st.error(str(e))
            else:
                st.session_state.followup_messages.append(
                    {"role": "user", "content": prompt}
                )
                st.session_state.followup_messages.append(
                    {"role": "assistant", "content": reply}
                )
                st.rerun()

st.caption(
    "Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `Summit-Hack-26/.env`. "
    "Optional: `GEMINI_MODEL` (default `gemini-2.5-flash`)."
)
