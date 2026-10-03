"""Dumb profile data. No methods with I/O or scoring."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ProfileStatus(str, Enum):
    OK = "ok"
    NEEDS_OCR = "needs_ocr"
    FAILED = "failed"


class Experience(BaseModel):
    title: str = ""
    company: str = ""
    years: float = 0.0
    summary: str = ""


class Education(BaseModel):
    degree: str = ""
    school: str = ""
    year: int | None = None


class ResumeRaw(BaseModel):
    """Raw extraction output. Separate from the LLM-built profile."""

    source_file: str
    file_hash: str  # sha256 of the file bytes (exact-duplicate detection)
    full_text: str = ""
    needs_ocr: bool = False
    content_hash: str = ""  # sha256 of normalized text (near-duplicate detection)


class CandidateProfile(BaseModel):
    id: str = Field(description="stable id, e.g. sha1 of file_hash")
    name: str = ""
    email: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    source_file: str = ""
    file_hash: str = ""
    profile_status: ProfileStatus = ProfileStatus.OK
    content_hash: str = ""  # normalized-text hash; drives rank-cache staleness
    resume_text: str = ""  # full extracted text; powers substring search
