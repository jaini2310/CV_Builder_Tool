import base64
import os
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .models import ExtractCvRequest, GenerateCvRequest, NextQuestionRequest

# Allow importing reusable business logic from the existing root project.
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from cv_generator import generate_docx, generate_pdf  # noqa: E402
from llm_service import extract_structured_cv, get_next_question, transcribe_audio  # noqa: E402
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/next-question")
def api_next_question(payload: NextQuestionRequest):
    try:
        question = get_next_question(
            messages=[msg.model_dump() for msg in payload.messages],
            has_profile_photo=payload.has_profile_photo,
            photo_offer_made=payload.photo_offer_made,
        )
        return {"question": question}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/extract-cv")
def api_extract_cv(payload: ExtractCvRequest):
    if not payload.conversation_text.strip():
        return {"structured_cv": None}

    try:
        extracted = extract_structured_cv(payload.conversation_text)
        structured = CVSchema.model_validate(extracted).model_dump()
        return {"structured_cv": structured}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/transcribe-audio")
async def api_transcribe_audio(audio_file: UploadFile = File(...)):
    try:
        data = await audio_file.read()
        transcript = transcribe_audio(data, audio_file.filename or "speech.wav")
        return {"transcript": transcript}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/generate-cv")
def api_generate_cv(payload: GenerateCvRequest):
    try:
        structured = payload.structured_cv or {}
        if payload.conversation_text.strip():
            extracted = extract_structured_cv(payload.conversation_text)
            extracted_structured = CVSchema.model_validate(extracted).model_dump()
            structured = _merge_prefer_existing(structured, extracted_structured)

        cv = CVSchema.model_validate(structured)
        validated = cv.model_dump()

        if payload.profile_photo_base64:
            validated["profile_photo_bytes"] = base64.b64decode(payload.profile_photo_base64)
        else:
            validated["profile_photo_bytes"] = b""

        export_format = (payload.export_format or "pdf").strip().lower()
        template_id = (payload.template_id or "custom").strip().lower()
        requested_name = (payload.file_name or "").strip()

        if export_format == "docx":
            output_name = requested_name if requested_name else None
            output_path = generate_docx(validated, output_name or "generated_cv.docx", template_id=template_id)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            output_name = requested_name if requested_name else None
            output_path = generate_pdf(validated, output_name, template_id=template_id)
            media_type = "application/pdf"

        filename = os.path.basename(output_path)
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
