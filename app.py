import base64
import hashlib
import time
from pathlib import Path

import streamlit as st

from cv_generator import generate_pdf
from llm_service import extract_structured_cv, get_next_question, transcribe_audio
from schema import CVSchema

st.set_page_config(page_title="NTT AI CV Dashboard", layout="wide")

LOGO_CANDIDATES = [
    Path("assets/ntt_data_logo.png"),
    Path("assets/NTT_Logo.png"),
    Path("assets/ntt_logo.png"),
    Path("assets/logo.png"),
]


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --bg-soft: #f7fbff;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-strong: rgba(255, 255, 255, 0.96);
            --line: rgba(125, 150, 182, 0.13);
            --ink: #0b1324;
            --muted: #4d6078;
            --brand: #0074c8;
            --brand-soft: rgba(0, 116, 200, 0.1);
            --accent: #14c7b0;
            --accent-soft: rgba(20, 199, 176, 0.14);
            --success: #16a34a;
            --shadow: 0 30px 80px rgba(7, 20, 42, 0.09);
        }
        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(0, 116, 200, 0.16), transparent 22%),
                radial-gradient(circle at 100% 0%, rgba(20, 199, 176, 0.12), transparent 20%),
                linear-gradient(180deg, #ffffff 0%, #f7fbff 50%, #f2f8ff 100%);
            background-size: 120% 120%;
            animation: pageFloat 16s ease-in-out infinite;
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: -20% -10% auto auto;
            width: 420px;
            height: 420px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.14) 0%, rgba(37, 99, 235, 0) 70%);
            filter: blur(6px);
            pointer-events: none;
            animation: blobDrift 18s ease-in-out infinite;
            z-index: 0;
        }
        .stApp::after {
            content: "";
            position: fixed;
            inset: auto auto -14% -10%;
            width: 460px;
            height: 460px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(15, 118, 110, 0.16) 0%, rgba(15, 118, 110, 0) 72%);
            filter: blur(10px);
            pointer-events: none;
            animation: blobDriftAlt 22s ease-in-out infinite;
            z-index: 0;
        }
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2rem;
            max-width: 1380px;
            position: relative;
            z-index: 1;
        }
        .dashboard-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 251, 255, 0.92) 55%, rgba(240, 255, 251, 0.84) 100%);
            border: 1px solid var(--line);
            border-radius: 30px;
            padding: 1.45rem 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            backdrop-filter: blur(18px);
        }
        .hero-shell {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at top right, rgba(0, 116, 200, 0.22), transparent 28%),
                radial-gradient(circle at bottom left, rgba(20, 199, 176, 0.12), transparent 24%),
                linear-gradient(135deg, rgba(255, 255, 255, 0.995) 0%, rgba(239, 250, 255, 0.96) 45%, rgba(238, 255, 248, 0.95) 100%);
        }
        .hero-shell::before {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            top: -110px;
            right: -80px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.18) 0%, rgba(37, 99, 235, 0) 72%);
            animation: haloPulse 8s ease-in-out infinite;
        }
        .hero-shell::after {
            content: "";
            position: absolute;
            inset: 0;
            background-image: linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(148, 163, 184, 0.06) 1px, transparent 1px);
            background-size: 28px 28px;
            opacity: 0.35;
            pointer-events: none;
        }
        .hero-content {
            position: relative;
            z-index: 1;
        }
        .hero-brand {
            display: flex;
            align-items: center;
            gap: 1.1rem;
            margin-bottom: 1.15rem;
            flex-wrap: wrap;
        }
        .hero-logo {
            width: 250px;
            max-width: 100%;
            height: auto;
            display: block;
        }
        .hero-brand-copy {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .hero-brand-title {
            color: #0f172a;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.01em;
        }
        .hero-brand-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.42rem 0.86rem;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(0, 116, 200, 0.12), rgba(20, 199, 176, 0.12));
            border: 1px solid rgba(0, 116, 200, 0.14);
            color: #075985;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            width: fit-content;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.4rem 0.8rem;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(0, 116, 200, 0.12), rgba(20, 199, 176, 0.1));
            color: #066799;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.85rem;
        }
        .hero-title {
            display: inline-block;
            width: fit-content;
            max-width: 100%;
            font-size: 3rem;
            line-height: 1.02;
            font-weight: 700;
            color: transparent;
            background: linear-gradient(90deg, #04172d 0%, #005da8 30%, #11b9a4 58%, #005da8 82%, #04172d 100%);
            background-size: 220% 100%;
            background-position: 0% 50%;
            -webkit-background-clip: text;
            background-clip: text;
            margin-bottom: 0.7rem;
            letter-spacing: -0.025em;
            animation: shimmerText 8s ease-in-out infinite alternate;
            text-shadow: 0 2px 10px rgba(0, 116, 200, 0.05);
        }
        .hero-copy {
            color: #3f536b;
            margin-bottom: 1.1rem;
            max-width: 760px;
            font-size: 1.05rem;
            line-height: 1.72;
            animation: fadeRise 0.9s ease-out both;
        }
        .hero-meta {
            display: flex;
            gap: 0.72rem;
            flex-wrap: wrap;
        }
        .hero-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 0.92rem;
            border-radius: 999px;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(240, 249, 255, 0.86));
            border: 1px solid rgba(125, 150, 182, 0.12);
            color: #36546f;
            font-size: 0.84rem;
            font-weight: 700;
            animation: fadeRise 1.05s ease-out both;
        }
        .hero-pill:nth-child(2) {
            animation-delay: 0.08s;
        }
        .hero-pill:nth-child(3) {
            animation-delay: 0.16s;
        }
        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 128px;
            background: linear-gradient(155deg, rgba(255,255,255,0.98), rgba(240,248,255,0.9)) !important;
        }
        .metric-card::before {
            content: "";
            position: absolute;
            width: 74px;
            height: 74px;
            border-radius: 999px;
            right: -16px;
            top: -16px;
            background: linear-gradient(135deg, rgba(0, 116, 200, 0.18), rgba(24, 183, 160, 0.12));
        }
        .metric-card::after {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #0074c8, #14c7b0);
        }
        .metric-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            background: rgba(0, 116, 200, 0.08);
            color: var(--accent);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.85rem;
        }
        .metric-value {
            color: var(--ink);
            font-size: 2.12rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.22rem;
        }
        .metric-subtle {
            color: var(--muted);
            font-size: 0.92rem;
        }
        .app-loader-shell {
            min-height: 72vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .app-loader-card {
            width: min(520px, 92vw);
            text-align: center;
            padding: 2rem 2.2rem;
            border-radius: 28px;
            border: 1px solid rgba(125, 150, 182, 0.16);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.97), rgba(240, 249, 255, 0.9));
            box-shadow: 0 24px 56px rgba(12, 35, 64, 0.1);
            backdrop-filter: blur(18px);
        }
        .app-loader-spinner {
            width: 56px;
            height: 56px;
            margin: 0 auto 1rem auto;
            border-radius: 999px;
            border: 4px solid rgba(0, 116, 200, 0.14);
            border-top-color: #0074c8;
            border-right-color: #11b9a4;
            animation: loaderSpin 0.9s linear infinite;
        }
        .app-loader-title {
            color: #0f172a;
            font-size: 1.18rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .app-loader-copy {
            color: #587089;
            font-size: 0.97rem;
            line-height: 1.65;
        }
        .section-title {
            color: var(--ink);
            font-size: 1.22rem;
            font-weight: 800;
            margin-bottom: 0.28rem;
        }
        .section-copy {
            color: var(--muted);
            margin-bottom: 0.4rem;
        }
        .panel-banner {
            margin-bottom: 0.8rem;
        }
        .panel-tag {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.82rem;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(0, 116, 200, 0.1), rgba(20, 199, 176, 0.1));
            color: #066799;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.55rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--line) !important;
            border-radius: 24px !important;
            background: linear-gradient(155deg, rgba(255,255,255,0.9), rgba(244,250,255,0.82)) !important;
            box-shadow: var(--shadow) !important;
            backdrop-filter: blur(18px);
        }
        div[data-testid="stChatMessage"] {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(240, 248, 255, 0.84));
            border: 1px solid rgba(125, 150, 182, 0.14);
            border-radius: 22px;
            padding: 0.24rem 0.35rem;
            box-shadow: 0 16px 36px rgba(12, 35, 64, 0.05);
            margin-bottom: 0.55rem;
        }
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
            line-height: 1.65;
        }
        div[data-testid="stForm"] {
            margin-top: 1rem;
            padding: 0.45rem 0.5rem;
            border-radius: 28px;
            border: 1px solid rgba(125, 150, 182, 0.16);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(239, 248, 255, 0.88));
            box-shadow: 0 12px 28px rgba(12, 35, 64, 0.06);
        }
        div[data-testid="stForm"] div[data-baseweb="input"] > div {
            min-height: 3.25rem;
            border-radius: 20px !important;
            border: 0 !important;
            background: rgba(255, 255, 255, 0.55) !important;
            box-shadow: none !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] input {
            font-size: 0.98rem !important;
            padding-left: 0.2rem !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] input:disabled {
            color: #7b8798 !important;
            -webkit-text-fill-color: #7b8798 !important;
            cursor: not-allowed !important;
        }
        div[data-testid="stForm"] div[data-baseweb="input"] > div:has(input:disabled) {
            background: linear-gradient(145deg, rgba(236, 241, 247, 0.95), rgba(227, 234, 243, 0.92)) !important;
            border: 1px solid rgba(125, 150, 182, 0.18) !important;
            opacity: 0.82;
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
            min-height: 3.25rem;
            border-radius: 20px !important;
            background: linear-gradient(135deg, #0074c8 0%, #11b9a4 100%) !important;
            border: 0 !important;
            color: #ffffff !important;
            box-shadow: 0 16px 30px rgba(0, 116, 200, 0.2);
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 20px 34px rgba(0, 116, 200, 0.24);
        }
        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:disabled,
        div[data-testid="stButton"] button:disabled {
            background: linear-gradient(145deg, #c6d1dd, #b8c5d3) !important;
            border: 0 !important;
            color: #f8fbff !important;
            box-shadow: none !important;
            opacity: 0.85;
            cursor: not-allowed !important;
            transform: none !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            border-radius: 18px !important;
            border-color: rgba(125, 150, 182, 0.2) !important;
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(243, 250, 255, 0.88)) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95);
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            color: var(--ink) !important;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 16px;
            min-height: 3rem;
            font-weight: 700;
            border: 1px solid rgba(125, 150, 182, 0.18);
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(240, 250, 255, 0.88));
            color: var(--ink);
            box-shadow: 0 14px 28px rgba(12, 35, 64, 0.06);
        }
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(0, 116, 200, 0.22);
            color: var(--ink);
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #19b983 0%, #0f9f66 100%);
            border: 1px solid #0f9f66;
            color: #ffffff;
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: linear-gradient(135deg, #10a36d 0%, #0b8a5b 100%);
            border-color: #0b8a5b;
            color: #ffffff;
        }
        @keyframes pageFloat {
            0% { background-position: 0% 0%; }
            50% { background-position: 50% 25%; }
            100% { background-position: 0% 0%; }
        }
        @keyframes blobDrift {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            50% { transform: translate3d(-30px, 20px, 0) scale(1.08); }
            100% { transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes blobDriftAlt {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            50% { transform: translate3d(24px, -18px, 0) scale(1.06); }
            100% { transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes haloPulse {
            0% { transform: scale(0.96); opacity: 0.7; }
            50% { transform: scale(1.08); opacity: 1; }
            100% { transform: scale(0.96); opacity: 0.7; }
        }
        @keyframes shimmerText {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }
        @keyframes fadeRise {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes loaderSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_text" not in st.session_state:
        st.session_state.conversation_text = ""
    if "structured_cv" not in st.session_state:
        st.session_state.structured_cv = None
    if "preview_error" not in st.session_state:
        st.session_state.preview_error = ""
    if "generated_cv_path" not in st.session_state:
        st.session_state.generated_cv_path = ""
    if "generated_cv_name" not in st.session_state:
        st.session_state.generated_cv_name = "cv.pdf"
    if "last_audio_fingerprint" not in st.session_state:
        st.session_state.last_audio_fingerprint = ""
    if "latest_transcript" not in st.session_state:
        st.session_state.latest_transcript = ""
    if "is_processing_reply" not in st.session_state:
        st.session_state.is_processing_reply = False
    if "pending_user_reply" not in st.session_state:
        st.session_state.pending_user_reply = ""
    if "chat_error" not in st.session_state:
        st.session_state.chat_error = ""
    if "ui_bootstrapped" not in st.session_state:
        st.session_state.ui_bootstrapped = False
    if not st.session_state.messages:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Hi! I will help you create your CV.\n\nWhat is your full name?",
            }
        )


def build_conversation_text(messages):
    user_lines = [f"User: {msg['content']}" for msg in messages if msg["role"] == "user"]
    return "\n".join(user_lines)


def sync_preview():
    conversation_text = build_conversation_text(st.session_state.messages)
    st.session_state.conversation_text = conversation_text

    if not conversation_text.strip():
        st.session_state.structured_cv = None
        st.session_state.preview_error = ""
        return

    try:
        extracted = extract_structured_cv(conversation_text)
        st.session_state.structured_cv = CVSchema.model_validate(extracted).model_dump()
        st.session_state.preview_error = ""
    except Exception as exc:
        st.session_state.preview_error = str(exc)


def process_user_reply(user_text):
    cleaned = user_text.strip()
    if not cleaned:
        return

    st.session_state.messages.append({"role": "user", "content": cleaned})
    next_question = get_next_question(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": next_question})
    sync_preview()


def queue_user_reply(user_text):
    cleaned = user_text.strip()
    if not cleaned:
        return

    st.session_state.pending_user_reply = cleaned
    st.session_state.is_processing_reply = True
    st.session_state.chat_error = ""


def generate_cv_file():
    sync_preview()
    structured = st.session_state.structured_cv or {}
    cv = CVSchema.model_validate(structured)
    safe_name = (cv.name or "candidate_cv").strip().replace(" ", "_")
    output_path = generate_pdf(cv.model_dump(), f"{safe_name}.pdf")
    st.session_state.generated_cv_path = output_path
    st.session_state.generated_cv_name = f"{safe_name}.pdf"


def calculate_completion(cv_data):
    if not cv_data:
        return 0

    checks = [
        bool(cv_data.get("name")),
        bool(cv_data.get("title")),
        bool(cv_data.get("total_it_experience")),
        bool(cv_data.get("summary")),
        bool(cv_data.get("skills")),
        bool(cv_data.get("experience")),
        bool(cv_data.get("education")),
        bool(cv_data.get("achievements")),
    ]
    return int(sum(checks) / len(checks) * 100)


def render_metric_card(label, value):
    st.markdown(
        f"""
        <div class="dashboard-card metric-card">
            <div class="metric-kicker">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtle">Live from the current conversation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_list(items, empty_message):
    if not items:
        st.caption(empty_message)
        return

    for item in items:
        st.write(f"- {item}")


def get_brand_logo_markup():
    for logo_path in LOGO_CANDIDATES:
        if logo_path.exists():
            suffix = logo_path.suffix.lower().lstrip(".") or "png"
            encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            return f'<img class="hero-logo" src="data:image/{suffix};base64,{encoded}" alt="NTT DATA logo" />'

    return """
        <svg class="hero-logo" viewBox="0 0 560 120" xmlns="http://www.w3.org/2000/svg" aria-label="NTT DATA logo" role="img">
            <g fill="none" stroke="#0080C9" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="54" cy="60" r="38"/>
                <circle cx="54" cy="24" r="15"/>
                <path d="M26 70c0-18 13-31 30-31 16 0 27 11 27 25 0 16-12 28-29 28-16 0-28-10-28-22"/>
            </g>
            <g fill="#0A6EBD">
                <text x="112" y="78" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="60" font-weight="900" letter-spacing="-3">NTT</text>
                <text x="250" y="78" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="60" font-weight="900" letter-spacing="-3">DATA</text>
            </g>
        </svg>
    """


inject_styles()
init_state()

if not st.session_state.ui_bootstrapped:
    st.markdown(
        """
        <div class="app-loader-shell">
            <div class="app-loader-card">
                <div class="app-loader-spinner"></div>
                <div class="app-loader-title">Tool is loading</div>
                <div class="app-loader-copy">
                    Preparing the NTT DATA Internal CV Studio and loading the workspace.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.7)
    st.session_state.ui_bootstrapped = True
    st.rerun()

structured_cv = st.session_state.structured_cv or {}
completion = calculate_completion(structured_cv)
user_responses = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
experience_items = len(structured_cv.get("experience", []))
skills_count = len(structured_cv.get("skills", []))

st.markdown(
    f"""
    <div class="dashboard-card hero-shell">
        <div class="hero-content">
        <div class="hero-brand">
            {get_brand_logo_markup()}
            <div class="hero-brand-copy">
                <div class="hero-brand-pill">NTT DATA Internal CV Studio</div>
            </div>
        </div>
        <div class="hero-title">Craft stronger NTT DATA profiles with clarity and impact.</div>
        <p class="hero-copy">
            Enable teams to capture consultant experience, skills, achievements, and project depth in a refined format for internal talent profiling and client-facing opportunities.
        </p>
        <div class="hero-meta">
            <span class="hero-pill">NTT DATA-ready resume flow</span>
            <span class="hero-pill">Voice-assisted profiling</span>
            <span class="hero-pill">Clean PDF export</span>
        </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric_card("Profile completion", f"{completion}%")
with metric_cols[1]:
    render_metric_card("User responses", user_responses)
with metric_cols[2]:
    render_metric_card("Skills captured", skills_count)
with metric_cols[3]:
    render_metric_card("Experience items", experience_items)

left_col, right_col = st.columns([1.35, 1], gap="large")

with left_col:
    st.markdown(
        """
        <div class="panel-banner">
            <div class="panel-tag">Live Interview</div>
            <div class="section-title">Conversation Workspace</div>
            <div class="section-copy">Ask and answer naturally. The assistant keeps building the CV structure in the background.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if hasattr(st, "audio_input"):
        st.markdown('<div class="panel-tag" style="margin-bottom:0.45rem;">Microphone</div>', unsafe_allow_html=True)
        recorded_audio = st.audio_input("Record a spoken answer", disabled=st.session_state.is_processing_reply)
        if recorded_audio is not None:
            audio_bytes = recorded_audio.getvalue()
            fingerprint = hashlib.sha256(audio_bytes).hexdigest()
            if fingerprint != st.session_state.last_audio_fingerprint:
                with st.spinner("Transcribing your audio..."):
                    try:
                        transcript = transcribe_audio(audio_bytes, recorded_audio.name or "speech.wav")
                        st.session_state.latest_transcript = transcript
                        st.session_state.last_audio_fingerprint = fingerprint
                    except Exception as exc:
                        st.session_state.latest_transcript = ""
                        st.error(f"Speech-to-text failed: {exc}")
    else:
        st.info("This Streamlit version does not support `st.audio_input`, so speech capture is unavailable.")

    if st.session_state.latest_transcript:
        st.text_area(
            "Latest transcript",
            value=st.session_state.latest_transcript,
            height=100,
            disabled=True,
        )
        if st.button("Use Transcript", use_container_width=True, disabled=st.session_state.is_processing_reply):
            queue_user_reply(st.session_state.latest_transcript)
            st.session_state.latest_transcript = ""
            st.rerun()

    with st.container(border=True):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    with st.form("chat_composer", clear_on_submit=True):
        composer_cols = st.columns([0.8, 0.2], gap="small")

        with composer_cols[0]:
            typed_reply = st.text_input(
                "Message",
                key="composer_text",
                label_visibility="collapsed",
                placeholder="Type your answer here",
                disabled=st.session_state.is_processing_reply,
            )

        with composer_cols[1]:
            send_clicked = st.form_submit_button("->", use_container_width=True, disabled=st.session_state.is_processing_reply)

    if send_clicked and typed_reply.strip():
        queue_user_reply(typed_reply)
        st.rerun()

with right_col:
    st.markdown(
        """
        <div class="panel-banner">
            <div class="panel-tag" style="background: var(--accent-soft); color: var(--accent);">Structured Output</div>
            <div class="section-title">CV Snapshot</div>
            <div class="section-copy">Review extracted details, spot missing information quickly, and export the final PDF when everything looks right.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Refresh Preview", use_container_width=True):
            sync_preview()
    with action_cols[1]:
        if st.button("Generate CV", type="primary", use_container_width=True):
            try:
                generate_cv_file()
                st.success("CV generated successfully.")
            except Exception as exc:
                st.error(str(exc))

    structured_cv = st.session_state.structured_cv or {}

    if st.session_state.preview_error:
        st.warning(f"Preview refresh issue: {st.session_state.preview_error}")

    with st.container(border=True):
        st.subheader(structured_cv.get("name") or "Candidate name pending")
        st.caption(structured_cv.get("title") or "Current title pending")
        if structured_cv.get("total_it_experience"):
            st.caption(f"Total IT experience: {structured_cv.get('total_it_experience')}")
        if structured_cv.get("objectives"):
            st.write(f"**Career objective:** {structured_cv.get('objectives')}")
        st.write(structured_cv.get("summary") or "Summary will appear here as the conversation grows.")

    preview_cols = st.columns(2)
    with preview_cols[0]:
        with st.container(border=True):
            st.markdown("**Skills**")
            render_list(structured_cv.get("skills", []), "No skills extracted yet.")
        with st.container(border=True):
            st.markdown("**Achievements**")
            render_list(structured_cv.get("achievements", []), "No achievements extracted yet.")
    with preview_cols[1]:
        with st.container(border=True):
            st.markdown("**Education**")
            education_items = structured_cv.get("education", [])
            if education_items:
                for item in education_items:
                    if isinstance(item, dict):
                        values = [str(value) for value in item.values() if value]
                        st.write(f"- {' | '.join(values)}")
                    else:
                        st.write(f"- {item}")
            else:
                st.caption("No education details extracted yet.")
        with st.container(border=True):
            st.markdown("**Certifications**")
            render_list(structured_cv.get("certifications", []), "No certifications extracted yet.")

    with st.container(border=True):
        st.markdown("**Experience**")
        experience = structured_cv.get("experience", [])
        if experience:
            for item in experience:
                role = item.get("role") or "Role pending"
                company = item.get("company") or "Company pending"
                st.write(f"**{role}** at **{company}**")
                dates = " - ".join(filter(None, [item.get("start_date"), item.get("end_date")]))
                if dates:
                    st.caption(dates)
                for responsibility in item.get("responsibilities", item.get("bullets", [])):
                    st.write(f"- {responsibility}")
        else:
            st.caption("No experience entries extracted yet.")

    if st.session_state.generated_cv_path:
        with open(st.session_state.generated_cv_path, "rb") as generated_file:
            st.download_button(
                "Download CV",
                data=generated_file.read(),
                file_name=st.session_state.generated_cv_name,
                mime="application/pdf",
                use_container_width=True,
            )

if st.session_state.chat_error:
    st.error(f"Chat response failed: {st.session_state.chat_error}")

if st.session_state.is_processing_reply and st.session_state.pending_user_reply:
    try:
        with st.spinner("Assistant is preparing the next question..."):
            process_user_reply(st.session_state.pending_user_reply)
        st.session_state.pending_user_reply = ""
        st.session_state.is_processing_reply = False
        st.rerun()
    except Exception as exc:
        st.session_state.pending_user_reply = ""
        st.session_state.is_processing_reply = False
        st.session_state.chat_error = str(exc)
        st.rerun()
