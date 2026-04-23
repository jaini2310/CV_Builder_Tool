import os
import json
import re
from io import BytesIO
import truststore
from openai import OpenAI
from dotenv import load_dotenv

# resolving cert issue when Open AI sendung response
truststore.inject_into_ssl()

# Prefer the project .env value over any stale shell/session variable.
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key:
    raise ValueError("OPENAI_API_KEY is missing. Add it to the project .env file.")

client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"   # replace if your enterprise model name is different
TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")


def get_next_question(messages, has_profile_photo=False, photo_offer_made=False):
    photo_status = "A profile photo has already been uploaded." if has_profile_photo else "No profile photo has been uploaded yet."
    photo_prompt_status = "The profile photo option has already been offered once." if photo_offer_made else "The profile photo option has not been offered yet."

    system_prompt = """
    You are a professional CV assistant.

    Ask the user one question at a time to collect CV details.
    Review the existing conversation before asking the next question.
    Do not skip any required field.

    Collect:
    - Career objective
    - Full name
    - Current role
    - Company
    - Total IT experience till date
    - Professional summary that reflects the candidate's complete IT experience
    - Skills
    - Education
    - Certifications
    - Achievements
    - Full work experience history with roles and responsibilities
    - Offer an optional profile photo upload once the main CV details are mostly collected

    Keep questions short and conversational.
    Career objective is mandatory, so make sure you ask for it before finishing.
    Total IT experience and professional summary are mandatory, so make sure both are collected clearly.
    The experience section should represent the candidate's complete IT experience till date, not only the current job.
    Ask about work experience in one consolidated question whenever possible.
    Do not ask separately for roles and responsibilities after the user has already shared them.
    If responsibilities are already available, ask only for the missing parts such as company name or dates.
    Ask explicitly for certifications. If the candidate has no certifications, capture that clearly as "none".
    The profile photo is optional. Ask about it at most once, and only after the required CV details have been substantially collected.
    If you ask about the profile photo, tell the user they can upload it using the profile photo uploader in the dashboard.
    Only say the final completion message after all required items have been collected.

    If enough information is collected, reply exactly:
    Thank you. Click 'Generate CV' to create your resume.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"{system_prompt}\n\nCurrent photo status: {photo_status}\n{photo_prompt_status}",
            }
        ]
        + messages,
        temperature=0.7,
    )

    return response.choices[0].message.content


def extract_structured_cv(conversation_text):
    system_prompt = """
    You are a JSON extractor assistant.

    Extract the CV information into strict JSON with these keys:
    objectives, name, title, total_it_experience, contact, location, summary, experience, education, skills, certifications, achievements

    Rules:
    - Return JSON only
    - objectives should capture the user's career objective statement when they mention phrases like "career objective", "objective", "my goal", or "my aim"
    - total_it_experience should capture the candidate's complete IT experience till date
    - summary should be a concise professional summary of the candidate's complete IT experience
    - experience should be a list of objects with:
      company, role, start_date, end_date, responsibilities
    - experience should include the candidate's complete relevant IT work history till date
    - education should be a list
    - skills, certifications, achievements should be lists
    - unknown values should be empty string or empty list
    """

    user_prompt = f"""
    Conversation:
    {conversation_text}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    text = response.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse JSON from model response:\n{text}")


def transcribe_audio(audio_bytes, filename="speech.wav"):
    if not audio_bytes or len(audio_bytes) < 1024:
        return ""

    audio_stream = BytesIO(audio_bytes)
    audio_stream.name = filename

    response = client.audio.transcriptions.create(
        model=TRANSCRIBE_MODEL,
        file=audio_stream,
        language="en",
    )

    transcript = getattr(response, "text", "").strip()
    return transcript
