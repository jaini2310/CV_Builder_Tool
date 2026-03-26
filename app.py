import hashlib

import streamlit as st

from cv_generator import generate_pdf
from llm_service import extract_structured_cv, get_next_question, transcribe_audio
from schema import CVSchema

st.set_page_config(page_title="NTT AI CV Dashboard", layout="wide")


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(29, 78, 216, 0.12), transparent 30%),
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 26%),
                linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        }
        .dashboard-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }
        .hero-copy {
            color: #334155;
            margin-bottom: 0;
        }
        .metric-label {
            color: #475569;
            font-size: 0.9rem;
        }
        .metric-value {
            color: #0f172a;
            font-size: 1.55rem;
            font-weight: 700;
        }
        .section-title {
            color: #0f172a;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }
        .section-copy {
            color: #475569;
            margin-bottom: 0.4rem;
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
        <div class="dashboard-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
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


inject_styles()
init_state()

structured_cv = st.session_state.structured_cv or {}
completion = calculate_completion(structured_cv)
user_responses = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
experience_items = len(structured_cv.get("experience", []))
skills_count = len(structured_cv.get("skills", []))

st.markdown(
    """
    <div class="dashboard-card">
        <div class="hero-title">Conversational CV Dashboard</div>
        <p class="hero-copy">
            Capture answers by typing or speaking, track CV completeness live, and generate a polished resume when ready.
        </p>
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
    st.markdown('<div class="section-title">Conversation Workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Answer the assistant by typing below or recording a spoken response.</div>',
        unsafe_allow_html=True,
    )

    if hasattr(st, "audio_input"):
        st.markdown("**Microphone**")
        recorded_audio = st.audio_input("Record a spoken answer")
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
        if st.button("Use Transcript", use_container_width=True):
            process_user_reply(st.session_state.latest_transcript)
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
                "Type your answer here",
                key="composer_text",
                label_visibility="collapsed",
                placeholder="Type your answer here",
            )

        with composer_cols[1]:
            send_clicked = st.form_submit_button("Send", use_container_width=True)

    if send_clicked and typed_reply.strip():
        process_user_reply(typed_reply)
        st.rerun()

with right_col:
    st.markdown('<div class="section-title">CV Snapshot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Preview what the assistant has extracted so far and generate the final document.</div>',
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
