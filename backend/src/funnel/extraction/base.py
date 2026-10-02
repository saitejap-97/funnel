"""Extraction contracts. No library imports here."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    page_no: int
    text: str = ""
    char_count: int = 0


class ExtractionResult(BaseModel):
    source_file: str
    pages: list[ExtractedPage] = Field(default_factory=list)
    full_text: str = ""

    @property
    def total_chars(self) -> int:
        return sum(p.char_count for p in self.pages)


class PdfTextExtractor(Protocol):
    def extract(self, path: Path) -> ExtractionResult: ...
