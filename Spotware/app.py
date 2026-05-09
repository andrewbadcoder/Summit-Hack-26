import json
import sys
from pathlib import Path

import streamlit as st

# Repo root (parent of Spotware/) so `perception` and `sustainability` resolve
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from perception import perceive  # noqa: E402
from sustainability import get_sustainability_record  # noqa: E402

# ── MUST be first Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="Spotware",
    page_icon="🔍",
    layout="centered",
)


# ── Fonts + Title Styling ────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700;800;900&display=swap');

        html, body, p, div, span, label, button, input {
            font-family: 'Inter', sans-serif !important;
        }

        .hero-title {
            font-family: 'DM Sans', sans-serif;
            font-size: clamp(5rem, 10vw, 9rem);
            font-weight: 900;
            text-align: center;
            letter-spacing: -0.03em;
            line-height: 1;
            width: 100%;
            padding: 2rem 0 0.5rem 0;
            color: inherit;
        }

        .hero-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 400;
            text-align: center;
            opacity: 0.6;
            margin-bottom: 2.5rem;
        }

        .hero-divider {
            border: none;
            border-top: 1px solid rgba(128,128,128,0.2);
            margin: 0 auto 2rem auto;
            width: 80%;
        }
    </style>
""",
    unsafe_allow_html=True,
)

_LOGO = Path(__file__).resolve().parent / "logo1.png"
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if _LOGO.is_file():
        st.image(str(_LOGO), width=200)

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
if "last_error" not in st.session_state:
    st.session_state.last_error = None

if image_bytes:
    run = st.button("Run analysis", type="primary")
    if run:
        st.session_state.last_error = None
        st.session_state.last_perception = None
        st.session_state.last_sustainability = None
        with st.spinner("Calling Gemini vision…"):
            try:
                perception = perceive(image_bytes)
                st.session_state.last_perception = perception
                st.session_state.last_sustainability = get_sustainability_record(
                    perception.get("device_class")
                )
            except Exception as e:
                st.session_state.last_error = str(e)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    per = st.session_state.last_perception
    sus = st.session_state.last_sustainability
    if per is not None and sus is not None:
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

        st.subheader("Sustainability snapshot")
        st.metric("Matched type", sus.get("component_type", "—"))
        m1, m2, m3 = st.columns(3)
        m1.metric("Embodied CO₂ (kg)", sus.get("embodied_co2_kg", "—"))
        m2.metric("Scrap value (USD)", sus.get("scrap_value_usd", "—"))
        gen = per.get("generation_hint", "unknown")
        refurb_key = (
            "refurb_value_modern_usd"
            if gen == "modern"
            else "refurb_value_legacy_usd"
            if gen == "legacy"
            else "refurb_value_modern_usd"
        )
        m3.metric("Refurb estimate (USD)", sus.get(refurb_key, "—"))
        metals = sus.get("recoverable_metals_g")
        if isinstance(metals, dict) and metals:
            st.write("**Recoverable metals (g)**")
            st.json(metals)
        flags = sus.get("hazard_flags")
        if isinstance(flags, list) and flags:
            st.warning("Hazard flags: " + ", ".join(str(x) for x in flags))
        if sus.get("default_action"):
            st.success(f"Suggested action: **{sus['default_action']}**")

        with st.expander("Raw perception JSON"):
            st.code(json.dumps(per, indent=2), language="json")
        with st.expander("Raw sustainability record"):
            st.code(json.dumps(sus, indent=2), language="json")

st.caption(
    "Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `Summit-Hack-26/.env`. "
    "Optional: `GEMINI_MODEL` (default `gemini-2.5-flash`)."
)
