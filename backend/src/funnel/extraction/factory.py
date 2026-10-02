"""Extractor wiring: primary pdfplumber, fallback pypdf on empty/error."""
from __future__ import annotations

from pathlib import Path

from funnel.extraction.base import ExtractionResult, PdfTextExtractor
from funnel.extraction.plumber import PlumberExtractor
from funnel.extraction.pypdf_extractor import PyPdfExtractor

MIN_CHARS_PRIMARY = 50  # below this, try fallback before flagging needs_ocr


class ChainedExtractor:
    """Tries primary, then fallback. Never raises on empty — flags need OCR."""

    def __init__(
        self,
        primary: PdfTextExtractor | None = None,
        fallback: PdfTextExtractor | None = None,
    ) -> None:
        self._primary = primary or PlumberExtractor()
        self._fallback = fallback or PyPdfExtractor()

    def extract(self, path: Path) -> ExtractionResult:
        try:
            result = self._primary.extract(path)
            if len(result.full_text.strip()) >= MIN_CHARS_PRIMARY:
                return result
        except Exception:
            result = None  # fall through to pypdf
        try:
            fb = self._fallback.extract(path)
            if fb.full_text.strip():
                return fb
            return result if result is not None else fb
        except Exception:
            if result is not None:
                return result
            raise


def build_extractor() -> ChainedExtractor:
    return ChainedExtractor()
