import base64
import os
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .models import ExtractCvRequest, GenerateCvRequest, NextQuestionRequest, SaveCvRequest, TranslateCvRequest

# Allow importing reusable business logic from the existing root project.
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from cv_generator import generate_docx, generate_pdf  # noqa: E402
from llm_service import apply_structured_cv_update, extract_structured_cv, get_next_question, transcribe_audio, translate_structured_cv  # noqa: E402
from schema import CVSchema  # noqa: E402

app = FastAPI(title="NTT CV Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _merge_prefer_existing(existing, extracted):
    if isinstance(existing, dict) and isinstance(extracted, dict):
        merged = {}
        for key in set(existing) | set(extracted):
            merged[key] = _merge_prefer_existing(existing.get(key), extracted.get(key))
        return merged

    if isinstance(existing, list):
        return existing if existing else (extracted or [])

    if existing not in (None, "", [], {}):
        return existing
    return extracted


def _merge_prefer_extracted(existing, extracted):
    if isinstance(existing, dict) and isinstance(extracted, dict):
        merged = {}
        for key in set(existing) | set(extracted):
            merged[key] = _merge_prefer_extracted(existing.get(key), extracted.get(key))
        return merged

    if isinstance(extracted, list):
        return extracted if extracted else (existing or [])

    if extracted not in (None, "", [], {}):
        return extracted
    return existing


def _get_last_user_text(conversation_text: str) -> str:
    user_lines = [line.strip() for line in conversation_text.splitlines() if line.strip().lower().startswith("user:")]
    if not user_lines:
        return conversation_text.strip()
    return user_lines[-1].split(":", 1)[-1].strip().lower()


def _is_edit_request(text: str) -> bool:
    return any(token in text for token in ["update", "edit", "change", "replace", "correct", "modify"])


SKILLS_FIELD_KEYWORDS = [
    "skill",
    "skills",
    "tech stack",
    "technology",
    "technologies",
    "java",
    "spring",
    "spring boot",
    "hibernate",
    "rest",
    "rest api",
    "microservice",
    "microservices",
    "api",
    "angular",
    "react",
    "python",
    "sql",
]


def _contains_any_keyword(text: str, keywords) -> bool:
    return any(keyword in text for keyword in keywords)


FIELD_KEYWORDS = {
    "objectives": ["objective", "career objective", "goal", "aim"],
    "name": ["name"],
    "title": ["title", "role", "designation", "position"],
    "total_it_experience": ["experience", "years of experience", "it experience"],
    "contact": ["contact", "email", "phone", "mobile", "linkedin", "website"],
    "location": ["location", "city", "address"],
    "summary": ["summary", "profile summary", "about me"],
    "skills": SKILLS_FIELD_KEYWORDS,
    "experience": ["experience", "company", "role", "project", "responsibilit", "employer", "worked"],
    "education": ["education", "degree", "college", "university", "school", "mca", "btech", "b.e", "bachelor", "master"],
    "certifications": ["certification", "certifications", "certificate"],
    "achievements": ["achievement", "achievements", "award"],
}


def _extract_updated_value(text: str) -> str:
    patterns = [
        r"\b(?:to|as)\b\s+(.+)$",
        r":\s*(.+)$",
        r"\b(?:is|are)\b\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .")
    return ""


def _split_list_values(value: str):
    if not value:
        return []
    parts = re.split(r",|\band\b|/|\|", value, flags=re.IGNORECASE)
    return [part.strip(" .") for part in parts if part.strip(" .")]


def _apply_simple_edit(existing_structured_cv: dict, last_user_text: str):
    updated = dict(existing_structured_cv or {})
    value = _extract_updated_value(last_user_text)
    if not value:
        return None

    if "name" in last_user_text:
        updated["name"] = value
        return updated
    if any(token in last_user_text for token in ["title", "role", "designation", "position"]):
        updated["title"] = value
        return updated
    if any(token in last_user_text for token in ["years of experience", "it experience", "total experience", "experience"]):
        if not any(token in last_user_text for token in ["certification", "achievement", "project", "company", "role and responsibilities"]) and not _contains_any_keyword(last_user_text, SKILLS_FIELD_KEYWORDS):
            updated["total_it_experience"] = value
            return updated
    if any(token in last_user_text for token in ["location", "city", "address"]):
        updated["location"] = value
        return updated
    if any(token in last_user_text for token in ["contact", "email", "phone", "mobile", "linkedin", "website"]):
        updated["contact"] = value
        return updated
    if any(token in last_user_text for token in ["summary", "profile summary", "about me"]):
        updated["summary"] = value
        return updated
    if _contains_any_keyword(last_user_text, SKILLS_FIELD_KEYWORDS):
        updated["skills"] = _split_list_values(value)
        return updated
    if "certification" in last_user_text or "certificate" in last_user_text:
        updated["certifications"] = _split_list_values(value)
        return updated
    if "achievement" in last_user_text or "award" in last_user_text:
        updated["achievements"] = _split_list_values(value)
        return updated

    return None


def _merge_with_edit_awareness(existing: dict, extracted: dict, conversation_text: str):
    last_user_text = _get_last_user_text(conversation_text)
    if not _is_edit_request(last_user_text):
        return _merge_prefer_existing(existing, extracted)

    merged = dict(existing or {})
    for key in set(existing or {}) | set(extracted or {}):
        existing_value = (existing or {}).get(key)
        extracted_value = (extracted or {}).get(key)
        keywords = FIELD_KEYWORDS.get(key, [])
        should_overwrite = _contains_any_keyword(last_user_text, keywords)

        if should_overwrite and extracted_value not in (None, "", [], {}):
            merged[key] = extracted_value
        else:
            merged[key] = _merge_prefer_existing(existing_value, extracted_value)
    return merged


def _resolve_structured_cv(conversation_text: str, existing_structured_cv: dict):
    existing_structured_cv = existing_structured_cv or {}
    last_user_text = _get_last_user_text(conversation_text)

    if _is_edit_request(last_user_text) and existing_structured_cv:
        simple_updated = _apply_simple_edit(existing_structured_cv, last_user_text)
        if simple_updated is not None:
            return CVSchema.model_validate(simple_updated).model_dump()

        updated = apply_structured_cv_update(existing_structured_cv, last_user_text)
        return CVSchema.model_validate(updated).model_dump()

    extracted = extract_structured_cv(conversation_text)
    extracted_structured = CVSchema.model_validate(extracted).model_dump()
    return _merge_with_edit_awareness(existing_structured_cv, extracted_structured, conversation_text)


def _extract_text_from_docx_bytes(data: bytes) -> str:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).replace(" \n ", "\n").strip()


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PDF resume import requires the `pypdf` package.") from exc

    reader = PdfReader(BytesIO(data))
    parts = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n".join(part for part in parts if part).strip()


def _extract_resume_text(filename: str, data: bytes) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".docx":
        return _extract_text_from_docx_bytes(data)
    if suffix == ".pdf":
        return _extract_text_from_pdf_bytes(data)
    raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported for import.")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/next-question")
def api_next_question(payload: NextQuestionRequest):
    try:
        question = get_next_question(
            messages=[msg.model_dump() for msg in payload.messages],
            structured_cv=payload.structured_cv,
            has_profile_photo=payload.has_profile_photo,
            photo_offer_made=payload.photo_offer_made,
            preferred_language=payload.preferred_language,
        )
        return {"question": question}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/extract-cv")
def api_extract_cv(payload: ExtractCvRequest):
    if not payload.conversation_text.strip():
        return {"structured_cv": payload.structured_cv or None}

    try:
        structured = _resolve_structured_cv(payload.conversation_text, payload.structured_cv or {})
        return {"structured_cv": structured}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/save-cv")
def api_save_cv(payload: SaveCvRequest):
    try:
        structured = CVSchema.model_validate(payload.structured_cv or {}).model_dump()
        return {"structured_cv": structured}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/translate-cv")
def api_translate_cv(payload: TranslateCvRequest):
    try:
        structured = CVSchema.model_validate(payload.structured_cv or {}).model_dump()
        translated = translate_structured_cv(structured, payload.target_language)
        validated = CVSchema.model_validate(translated).model_dump()
        return {"structured_cv": validated}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/import-resume")
async def api_import_resume(resume_file: UploadFile = File(...), preferred_language: str = Form("English")):
    try:
        data = await resume_file.read()
        if not data:
            raise HTTPException(status_code=400, detail="The uploaded resume file was empty.")

        extracted_text = _extract_resume_text(resume_file.filename or "resume.pdf", data)
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text was found in the uploaded resume.")

        extracted = extract_structured_cv(extracted_text)
        structured = CVSchema.model_validate(extracted).model_dump()
        next_question = get_next_question(
            messages=[],
            structured_cv=structured,
            has_profile_photo=False,
            photo_offer_made=False,
            preferred_language=preferred_language,
        )
        return {
            "structured_cv": structured,
            "next_question": next_question,
            "file_name": resume_file.filename or "resume",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/transcribe-audio")
async def api_transcribe_audio(audio_file: UploadFile = File(...), transcription_language: str = Form("")):
    try:
        data = await audio_file.read()
        transcript = transcribe_audio(data, audio_file.filename or "speech.wav", transcription_language or None)
        return {"transcript": transcript}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/generate-cv")
def api_generate_cv(payload: GenerateCvRequest):
    try:
        structured = payload.structured_cv or {}
        if payload.conversation_text.strip():
            structured = _resolve_structured_cv(payload.conversation_text, structured)

        cv = CVSchema.model_validate(structured)
        validated = cv.model_dump()

        export_format = (payload.export_format or "pdf").strip().lower()
        template_id = (payload.template_id or "custom").strip().lower()
        requested_name = (payload.file_name or "").strip()
        output_language = (payload.output_language or "English").strip() or "English"

        if not payload.skip_translation:
            validated = CVSchema.model_validate(translate_structured_cv(validated, output_language)).model_dump()

        if payload.profile_photo_base64:
            validated["profile_photo_bytes"] = base64.b64decode(payload.profile_photo_base64)
        else:
            validated["profile_photo_bytes"] = b""

        if export_format == "docx":
            output_name = requested_name if requested_name else None
            output_path = generate_docx(validated, output_name or "generated_cv.docx", template_id=template_id, output_language=output_language)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            output_name = requested_name if requested_name else None
            output_path = generate_pdf(validated, output_name, template_id=template_id, output_language=output_language)
            media_type = "application/pdf"

        filename = os.path.basename(output_path)
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
