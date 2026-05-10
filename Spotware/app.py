import json
import sys
import base64
import datetime
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

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
    layout="wide",
)
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
if "input_mode" not in st.session_state:
    st.session_state.input_mode = None
if "show_uploader" not in st.session_state:        # ← ADD THIS LINE
    st.session_state.show_uploader = False   
if "device_history" not in st.session_state:
    st.session_state.device_history = []

# ── File-backed analysis counter ─────────────────────────────────────────────
_COUNTER_FILE = Path(__file__).resolve().parent / ".analysis_count"

def _get_count() -> int:
    try:
        return int(_COUNTER_FILE.read_text().strip())
    except Exception:
        return 0

def _increment_count() -> int:
    c = _get_count() + 1
    try:
        _COUNTER_FILE.write_text(str(c))
    except Exception:
        pass
    return c

# ── Demo image ────────────────────────────────────────────────────────────────
_DEMO = Path(__file__).resolve().parent / "demo.jpg"
demo_b64 = ""
if _DEMO.is_file():
    demo_b64 = base64.b64encode(_DEMO.read_bytes()).decode()

# ── Fonts + Title Styling ────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700;800;900&display=swap');

    html, body, [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stMarkdown"] {
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    [data-testid="stHeader"]           { background-color: #0d1117 !important; }
    [data-testid="stSidebar"]          { background-color: #0a0f18 !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 4rem !important;
        max-width: 860px !important;
        margin: 0 auto !important;
        overflow-x: clip !important;
    }

.spotware-hero {
        text-align: center;
        padding: 3.5rem 0 1rem 0;
        width: 100vw;
        position: relative;
        left: 50%;
        transform: translateX(-50%);
        overflow: visible;
    }
    .spotware-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 10vw;
        font-weight: 900;
        text-align: center;
        letter-spacing: -0.05em;
        line-height: 1.0;
        color: #f0ede6;
        margin: 0 0 1.2rem 0;
        white-space: nowrap;
        display: block;
        width: 100%;
    }
    .spotware-subtitle {
        font-size: 0.92rem;
        color: #6b7280;
        margin: 0;
        padding-top: 0.5rem;
        display: block;
    }

    .sw-card {
        background: #161b22;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.5rem 1.75rem 1.75rem 1.75rem;
        margin: 1.5rem 0 1rem 0;
    }

    .sw-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-top: 0.75rem;
    }
    .sw-status-ready   { background: rgba(67,180,80,0.15);  color: #4db85c; }
    .sw-status-waiting { background: rgba(186,117,23,0.18); color: #c98d2a; }

    .panel {
        background: #161b22;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }
        .panel-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #58a6ff;
        margin-bottom: 0.75rem;
    }

    .result-card {
        background: #0d1117;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.88rem;
        color: #8b949e;
        line-height: 1.9;
    }
    .step-row {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.82rem;
        margin-bottom: 4px;
        color: #58a6ff;
    }
    .step-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #01969e;
        flex-shrink: 0;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.70rem !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: #58a6ff !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.4rem !important;
        color: #f0ede6 !important;
    }

    h2, h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em !important;
        color: #f0ede6 !important;
    }

    [data-testid="stBaseButton-primary"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background: #e5533d !important;
        color: #fff !important;
        border: none !important;
        border-radius: 999px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 0.75rem 1.5rem !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background: #cf3f2b !important;
    }

    [data-testid="stExpander"] {
        background: #161b22 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] summary p {
        font-weight: 600 !important;
        color: #8b949e !important;
    }

    [data-testid="stChatMessage"] {
        background: #161b22 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 10px !important;
    }

    [data-testid="stCaptionContainer"] p {
        color: #4f6a80 !important;
        font-size: 0.75rem !important;
    }

    .chat-history-item {
        background: #161b22;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
        font-size: 0.82rem;
        line-height: 1.5;
    }
    .chat-history-item .role-user {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #58a6ff;
        margin-bottom: 3px;
    }
    .chat-history-item .role-assistant {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #4db85c;
        margin-bottom: 3px;
    }
    .chat-history-item .msg-text { color: #8b949e; }
    .sidebar-section-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: #f0ede6;
        margin: 0.5rem 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .sidebar-empty {
        color: #2e4558;
        font-size: 0.82rem;
        font-style: italic;
        padding: 0.5rem 0;
    }

hr { border-color: rgba(255,255,255,0.07) !important; }

    /* ── Counter badge ── */
    .sw-counter {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(88,166,255,0.08);
        border: 1px solid rgba(88,166,255,0.18);
        border-radius: 999px; padding: 5px 16px;
        font-size: 0.78rem; font-weight: 600;
        color: #58a6ff; letter-spacing: 0.03em;
        margin-top: 0.9rem;
    }
    .sw-counter-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #58a6ff; animation: pulse-blue 2s infinite;
    }
    @keyframes pulse-blue {
        0%,100% { opacity:1; transform:scale(1); }
        50%      { opacity:0.4; transform:scale(1.4); }
    }

    /* ── How it works ── */
    .hiw-row { display: flex; gap: 1.25rem; margin: 0.5rem 0 0.25rem 0; }
    .hiw-step {
        flex: 1; background: #0d1117;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px; padding: 1rem 1.1rem; text-align: center;
    }
    .hiw-num { font-family:'DM Sans',sans-serif; font-size:1.6rem; font-weight:900; color:#e5533d; line-height:1; margin-bottom:0.4rem; }
    .hiw-label { font-size:0.78rem; font-weight:600; color:#f0ede6; margin-bottom:0.2rem; }
    .hiw-desc { font-size:0.72rem; color:#6b7280; }

    /* ── Drag-drop zone ── */
    .sw-dropzone {
        border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px;
        padding: 2.5rem 1.5rem; text-align: center; margin-bottom: 1.25rem;
        background: rgba(255,255,255,0.02); transition: border-color 0.2s, background 0.2s;
    }
    .sw-dropzone:hover, .sw-dropzone.dragover {
        border-color: #e5533d; background: rgba(229,83,61,0.05);
    }

    /* ── Confidence bar ── */
    .conf-bar-wrap {
        background: rgba(255,255,255,0.06); border-radius: 999px;
        height: 8px; width: 100%; margin: 6px 0 2px 0; overflow: hidden;
    }
    .conf-bar-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
    .conf-label {
        font-size: 0.7rem; color: #6b7280; margin-bottom: 3px;
        font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
    }

    /* ── History thumbnails ── */
    .hist-item {
        display: flex; gap: 0.6rem; align-items: center;
        background: #161b22; border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px; padding: 0.55rem 0.75rem; margin-bottom: 0.5rem;
    }
    .hist-thumb { width:40px; height:40px; border-radius:6px; object-fit:cover; flex-shrink:0; background:#0d1117; }
    .hist-info { flex:1; min-width:0; }
    .hist-device { font-size:0.75rem; font-weight:600; color:#f0ede6; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .hist-action { font-size:0.68rem; color:#6b7280; }
    .hist-ts { font-size:0.62rem; color:#3d5166; }

    /* ── Secondary button ── */
    [data-testid="stBaseButton-secondary"] {
        background: rgba(255,255,255,0.04) !important; color: #8b949e !important;
        border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 999px !important;
        font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important; font-weight: 600 !important;
    }
    [data-testid="stBaseButton-secondary"]:hover { background: rgba(255,255,255,0.08) !important; color: #f0ede6 !important; }
    /* ── File uploader styled as primary button ── */
    [data-testid="stFileUploadDropzone"] {
        background: rgba(255,255,255,0.02) !important;
        border: 2px dashed rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        padding: 2.5rem 1.5rem !important;
        text-align: center !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #e5533d !important;
        background: rgba(229,83,61,0.05) !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: #e5533d !important;
        color: #fff !important;
        border: none !important;
        border-radius: 999px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        padding: 0.5rem 1.5rem !important;
        margin-top: 0.75rem !important;
    }
    [data-testid="stFileUploadDropzone"] button:hover {
        background: #cf3f2b !important;
    }
</style>

""", unsafe_allow_html=True)
# ── Logo + Sidebar ────────────────────────────────────────────────────────────
_LOGO = Path(__file__).resolve().parent / "logo1.png"
logo_b64 = ""
if _LOGO.is_file():
    logo_b64 = base64.b64encode(_LOGO.read_bytes()).decode()

with st.sidebar:
    if logo_b64:
# ✅ No inline style — CSS class now fully controls size and glow
        st.markdown(        
            f"""<div class='sw-logo-wrap'>
                <img src='data:image/png;base64,{logo_b64}' alt='SpotWare'>
            </div>""",
            unsafe_allow_html=True,
        )

    # Device history
    st.markdown("<div class='sidebar-section-title'>🕓 Device History</div>", unsafe_allow_html=True)
    history = st.session_state.device_history
    if not history:
        st.markdown("<div class='sidebar-empty'>No devices analyzed yet.</div>", unsafe_allow_html=True)
    else:
        for entry in reversed(history[-5:]):
            per_h = entry.get("perception", {})
            dec_h = entry.get("decision", {})
            img_h = entry.get("image_b64", "")
            ts_h  = entry.get("timestamp", "")
            label  = dec_h.get("label", "—") if dec_h else "—"
            device = f"{per_h.get('manufacturer','?')} {per_h.get('model','?')}"
            thumb  = (f"<img class='hist-thumb' src='data:image/jpeg;base64,{img_h}'>"
                      if img_h else "<div class='hist-thumb'></div>")
            st.markdown(
                f"""<div class='hist-item'>{thumb}
                    <div class='hist-info'>
                        <div class='hist-device'>{device}</div>
                        <div class='hist-action'>{label}</div>
                        <div class='hist-ts'>{ts_h}</div>
                    </div></div>""",
                unsafe_allow_html=True,
            )
        if st.button("🗑️ Clear history", key="clear_hist", use_container_width=True):
            st.session_state.device_history = []
            st.rerun()

    # Follow-up chat history
    st.markdown("<div class='sidebar-section-title'>💬 Follow up history</div>", unsafe_allow_html=True)
    msgs = st.session_state.followup_messages
    if not msgs:
        st.markdown("<div class='sidebar-empty'>No questions asked yet.</div>", unsafe_allow_html=True)
    else:
        for msg in msgs:
            role_class = "role-user" if msg["role"] == "user" else "role-assistant"
            role_label = "You" if msg["role"] == "user" else "Spotware"
            st.markdown(
                f"""<div class='chat-history-item'>
                    <div class='{role_class}'>{role_label}</div>
                    <div class='msg-text'>{msg["content"]}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        if st.button("🗑️ Clear chat", key="clear_chat", use_container_width=True):
            st.session_state.followup_messages = []
            st.rerun()

# ── Hero (sticky, shrinks on scroll) ─────────────────────────────────────────


analysis_count = _get_count()
st.markdown(f"""
<div class="spotware-hero">
    <span class="spotware-title">SpotWare</span>
    <p class="spotware-subtitle">Upload or capture a photo of hardware for perception + sustainability lookup.</p>
    <div style='display:flex;justify-content:center;margin-top:0.9rem;'>
        <span class='sw-counter'>
            <span class='sw-counter-dot'></span>
            {analysis_count:,} device{"s" if analysis_count != 1 else ""} analyzed
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️  How it works"):
    st.markdown("""
<div class='hiw-row'>
  <div class='hiw-step'>
    <div class='hiw-num'>1</div>
    <div class='hiw-label'>Upload</div>
    <div class='hiw-desc'>Drop or capture a photo of any hardware — laptop, phone, server, PCB, etc.</div>
  </div>
  <div class='hiw-step'>
    <div class='hiw-num'>2</div>
    <div class='hiw-label'>Analyze</div>
    <div class='hiw-desc'>Gemini Vision identifies the device class, manufacturer, model, and physical condition.</div>
  </div>
  <div class='hiw-step'>
    <div class='hiw-num'>3</div>
    <div class='hiw-label'>Act</div>
    <div class='hiw-desc'>The decision engine recommends the best action: resell, repair, recycle, or dispose.</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ✅ AFTER — uploader hidden until "Add file" is clicked
col_up, col_cam = st.columns(2)
with col_up:
    if st.button(
        "📁  Add file" if not st.session_state.show_uploader else "✕  Cancel",
        key="btn_add_file",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.show_uploader = not st.session_state.show_uploader
        # If hiding, clear any prior upload state
        if not st.session_state.show_uploader:
            st.session_state.input_mode = None
        st.rerun()

with col_cam:
    if st.button("📷  Take a photo", key="btn_camera", use_container_width=True, type="primary"):
        st.session_state.input_mode = (
            None if st.session_state.input_mode == "camera" else "camera"
        )
        st.session_state.show_uploader = False   # collapse uploader if open
        st.rerun()

# ✅ Upload: widget, preview, and image_bytes all resolved in the same run
image_bytes: bytes | None = None
mime_hint: str | None = None
source_label = ""
if st.session_state.input_mode == "upload_top":
    _f = st.session_state.get("top_uploader")
    if _f is not None:
        image_bytes  = _f.getvalue()
        mime_hint    = _f.type or None
        source_label = _f.name
if st.session_state.show_uploader:
    
    uploaded_file_top = st.file_uploader(
        "Choose an image…",
        type=["jpg", "jpeg", "png"],
        help="JPG or PNG · max 200 MB",
        label_visibility="collapsed",
        key="top_uploader",
    )
    if uploaded_file_top is not None:
        # ✅ Read bytes immediately in this same run — no rerun needed
        image_bytes  = uploaded_file_top.getvalue()
        mime_hint    = uploaded_file_top.type or None
        source_label = uploaded_file_top.name
        st.session_state.input_mode = "upload_top"
        col_img, col_info = st.columns([2, 1])
        with col_img:
            st.image(uploaded_file_top, caption="Uploaded image", use_container_width=True)
        with col_info:
            size_kb = len(image_bytes) / 1024
            st.markdown(
                f"""<div class='result-card'>
                    <strong>File info</strong><br>
                    📄 {uploaded_file_top.name}<br>
                    📦 {size_kb:.1f} KB<br>
                    🖼️ {uploaded_file_top.type or "unknown type"}
                </div>""",
                unsafe_allow_html=True,
            )

if demo_b64:
    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    if st.button("🧪  Try a demo image", key="btn_demo", use_container_width=True):
        st.session_state.input_mode = "demo"
        st.rerun()
else:
    st.caption("💡 Add a `demo.jpg` to your app folder to enable the demo image button.")

st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

# ── File upload or camera — only shown after button click ─────────────────────


if st.session_state.input_mode == "demo":
    image_bytes  = base64.b64decode(demo_b64)
    mime_hint    = "image/jpeg"
    source_label = "demo.jpg"
    st.image(image_bytes, caption="Demo image", use_container_width=True)
    st.caption("This is a bundled demo image. Upload your own hardware photo for a real analysis.")

elif st.session_state.input_mode == "camera":
    picture = st.camera_input("Take a picture", help="Click the shutter button to capture a frame.")
    if picture is not None:
        image_bytes = picture.getvalue()
        mime_hint = picture.type or None
        source_label = "camera"
        col_img, col_info = st.columns([2, 1])
        with col_img:
            st.image(picture, caption="Camera capture", use_container_width=True)
        with col_info:
            size_kb = len(image_bytes) / 1024
            st.markdown(
                f"""<div class='result-card'>
                    <strong>Capture info</strong><br>
                    📸 Live webcam<br>
                    📦 {size_kb:.1f} KB<br>
                    🖼️ {picture.type or "image/jpeg"}
                </div>""",
                unsafe_allow_html=True,
            )

# Status badge
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
if image_bytes:
    st.markdown("<span class='sw-status sw-status-ready'>● Image ready</span>", unsafe_allow_html=True)
else:
    st.markdown("<span class='sw-status sw-status-waiting'>● Waiting for image</span>", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)  # close sw-card

if image_bytes:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    col_run, col_clear = st.columns([3, 1])
    with col_run:
        run = st.button("🔍  Run analysis", type="primary", use_container_width=True)
    with col_clear:
        clear = st.button("🗑️  Clear results", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if clear:
        st.session_state.last_error = None
        st.session_state.last_perception = None
        st.session_state.last_sustainability = None
        st.session_state.last_decision = None
        st.session_state.followup_messages = []
        st.session_state.input_mode = None        # ← ADD
        st.session_state.show_uploader = False    # ← ADD
        st.rerun()

    if run:
        st.session_state.last_error = None
        st.session_state.last_perception = None
        st.session_state.last_sustainability = None
        st.session_state.last_decision = None
        st.session_state.followup_messages = []
        progress_placeholder = st.empty()
        progress_placeholder.markdown(
            "<div class='step-row'><span class='step-dot'></span> Sending image to Gemini Vision…</div>",
            unsafe_allow_html=True,
        )
        with st.spinner("Analysing hardware…"):
            try:
                perception = perceive(image_bytes)
                progress_placeholder.markdown(
                    "<div class='step-row'><span class='step-dot'></span> Perception complete · fetching sustainability record…</div>",
                    unsafe_allow_html=True,
                )
                sustainability = get_sustainability_record(perception.get("device_class"))
                progress_placeholder.markdown(
                    "<div class='step-row'><span class='step-dot'></span> Sustainability fetched · running decision engine…</div>",
                    unsafe_allow_html=True,
                )
                decision = recommend_action(perception, sustainability)
                st.session_state.last_perception = perception
                st.session_state.last_sustainability = sustainability
                st.session_state.last_decision = decision
                progress_placeholder.empty()
                _increment_count()
                st.session_state.device_history.append({
                    "perception": perception,
                    "decision":   decision,
                    "image_b64":  base64.b64encode(image_bytes).decode(),
                    "timestamp":  datetime.datetime.now().strftime("%b %d, %H:%M"),
                })
                if len(st.session_state.device_history) > 5:
                    st.session_state.device_history = st.session_state.device_history[-5:]
            except Exception as e:
                st.session_state.last_error = str(e)
                progress_placeholder.empty()

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    per = st.session_state.last_perception
    sus = st.session_state.last_sustainability
    dec = st.session_state.last_decision
    if per is not None and sus is not None and dec is not None:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>🔎 Identification</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Device class", per.get("device_class", "—"))
        c2.metric("Manufacturer",  per.get("manufacturer",  "—"))
        c3.metric("Model",         per.get("model",         "—"))
        conf = per.get("confidence", 0)
        bar_color  = "#4db85c" if conf >= 0.8 else "#c98d2a" if conf >= 0.5 else "#e5533d"
        conf_label = "High confidence" if conf >= 0.8 else "Medium confidence" if conf >= 0.5 else "Low confidence"
        st.markdown(
            f"""<div style='margin-top:0.75rem;'>
                <div class='conf-label'>Confidence — {conf:.0%} · {conf_label}</div>
                <div class='conf-bar-wrap'>
                    <div class='conf-bar-fill' style='width:{conf*100:.1f}%;background:{bar_color};'></div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.caption(f"Condition: **{per.get('condition','—')}** · Completeness: **{per.get('completeness','—')}**")
        if per.get("notes"):
            st.info(per["notes"])
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Recommended action (the headline) ─────────────────────────────────
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>✅ Recommended action</div>", unsafe_allow_html=True)
        _ACTION_COLORS = {
            "green": ("#1a3a12", "#a8d87a", "#6db84a", "#4a8f2a"),
            "blue":  ("#0d2540", "#7ab8e8", "#4a90d0", "#2a68a8"),
            "amber": ("#3a2a08", "#e8c46a", "#c8942a", "#a86a0a"),
            "red":   ("#3a0d0d", "#e87a7a", "#c84a4a", "#a82a2a"),
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
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Sustainability impact ─────────────────────────────────────────────
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>♻️ Sustainability impact</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("CO₂ avoided",       f"{dec.get('co2_avoided_kg', 0)} kg",
                  help="Estimated kg of CO₂ avoided vs landfill disposal.")
        m2.metric("Recovery value",     f"${dec.get('value_usd', 0)}",
                  help="Estimated USD market or material recovery value.")
        m3.metric("Recoverable metals", f"{dec.get('metals_total_g', 0):.0f} g",
                  help="Total grams of recoverable metals (gold, copper, aluminium, etc.).")
        if dec.get("source"):
            st.caption(f"📚 Source: {dec['source']}")
        metals = dec.get("metals_breakdown_g") or sus.get("recoverable_metals_g")
        if isinstance(metals, dict) and metals:
            with st.expander("🪙  Metal breakdown"):
                metal_cols = st.columns(len(metals))
                for col, (metal, grams) in zip(metal_cols, metals.items()):
                    col.metric(metal.capitalize(), f"{grams} g")
        flags = sus.get("hazard_flags")
        if isinstance(flags, list) and flags:
            st.warning("⚠️  Hazard flags: " + ", ".join(str(x) for x in flags))
        st.markdown("</div>", unsafe_allow_html=True)

        flags = sus.get("hazard_flags")
        if isinstance(flags, list) and flags:
            st.warning("Hazard flags: " + ", ".join(str(x) for x in flags))

        # ── Why this recommendation? (rule trace) ─────────────────────────────
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>🧠 Decision & raw data</div>", unsafe_allow_html=True)
        with st.expander("Why this recommendation?"):
            st.markdown("**Decision logic trace**")
            for step in dec.get("rule_trace", []):
                st.markdown(f"- {step}")
            st.markdown(f"\n**Final action:** `{dec.get('action', '—')}`")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            with st.expander("Raw perception JSON"):
                st.code(json.dumps(per, indent=2), language="json")
        with col_b:
            with st.expander("Raw sustainability record"):
                st.code(json.dumps(sus, indent=2), language="json")
        with col_c:
            with st.expander("Raw decision output"):
                st.code(json.dumps(dec, indent=2), language="json")
        report_lines = [
            "SpotWare Analysis Report", "=" * 40,
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
            "DEVICE IDENTIFICATION",
            f"  Class:        {per.get('device_class','—')}",
            f"  Manufacturer: {per.get('manufacturer','—')}",
            f"  Model:        {per.get('model','—')}",
            f"  Condition:    {per.get('condition','—')}",
            f"  Confidence:   {per.get('confidence',0):.0%}", "",
            "RECOMMENDED ACTION",
            f"  {dec.get('label','—')}",
            f"  {dec.get('reason','')}", "",
            "SUSTAINABILITY IMPACT",
            f"  CO2 avoided:        {dec.get('co2_avoided_kg',0)} kg",
            f"  Recovery value:     ${dec.get('value_usd',0)}",
            f"  Recoverable metals: {dec.get('metals_total_g',0):.0f} g", "",
            "DECISION TRACE",
        ] + [f"  - {s}" for s in dec.get("rule_trace", [])]
        st.download_button(
            label="⬇️  Export report (.txt)",
            data="\n".join(report_lines),
            file_name=f"spotware_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>💬 Follow-up questions</div>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
