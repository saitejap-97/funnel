"""Dumb job-description data. No I/O, no logic."""
from __future__ import annotations

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    id: str = Field(description="stable id, e.g. sha1 of file_hash")
    title: str = ""
    source_file: str = ""
    file_hash: str = ""
    full_text: str = ""
