# schema.py
from typing import Any, Dict, List, Optional, Union
from pydantic import AliasChoices, BaseModel, Field, field_validator


class ExperienceItem(BaseModel):
    company: Optional[str] = ""
    role: Optional[str] = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    responsibilities: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("responsibilities", "bullets"),
    )

    @field_validator("responsibilities", mode="before")
    @classmethod
    def normalize_responsibilities(cls, value):
        if value in (None, ""):
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        return value


class CVSchema(BaseModel):
    objectives: Optional[str] = ""
    name: Optional[str] = ""
    title: Optional[str] = ""
    total_it_experience: Optional[str] = ""
    contact: Optional[str] = ""
    location: Optional[str] = ""
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
