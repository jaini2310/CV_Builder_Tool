from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class NextQuestionRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    structured_cv: Dict[str, Any] = Field(default_factory=dict)
    has_profile_photo: bool = False
    photo_offer_made: bool = False
    preferred_language: str = "English"


class ExtractCvRequest(BaseModel):
    conversation_text: str = ""
    structured_cv: Dict[str, Any] = Field(default_factory=dict)


class GenerateCvRequest(BaseModel):
    structured_cv: Dict[str, Any] = Field(default_factory=dict)
    conversation_text: str = ""
    profile_photo_base64: Optional[str] = None
    file_name: Optional[str] = None
    export_format: str = "pdf"
    template_id: str = "custom"


class SaveCvRequest(BaseModel):
    structured_cv: Dict[str, Any] = Field(default_factory=dict)
