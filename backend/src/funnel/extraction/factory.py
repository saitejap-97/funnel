"""Extractor wiring: primary pdfplumber, fallback pypdf on empty/error."""
from __future__ import annotations

import re
from pathlib import Path

from funnel.extraction.base import ExtractionResult, PdfTextExtractor
from funnel.extraction.plumber import PlumberExtractor
from funnel.extraction.pypdf_extractor import PyPdfExtractor

MIN_CHARS_PRIMARY = 50  # below this, try fallback before flagging needs_ocr

_CID_RE = re.compile(r"\(cid:\d+\)")


def _clean(text: str) -> str:
    """Normalize common PDF text artifacts (unmapped glyphs like bullets)."""
    return _CID_RE.sub("•", text)


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
                return _sanitized(result)
        except Exception:
            result = None  # fall through to pypdf
        try:
            fb = self._fallback.extract(path)
            if fb.full_text.strip():
                return _sanitized(fb)
            return _sanitized(result) if result is not None else _sanitized(fb)
        except Exception:
            if result is not None:
                return _sanitized(result)
            raise


def _sanitized(result: ExtractionResult) -> ExtractionResult:
    pages = [
        p.model_copy(update={"text": _clean(p.text)}) for p in result.pages
    ]
    return result.model_copy(
        update={
            "pages": pages,
            "full_text": _clean(result.full_text),
        }
    )


def build_extractor() -> ChainedExtractor:
    return ChainedExtractor()
