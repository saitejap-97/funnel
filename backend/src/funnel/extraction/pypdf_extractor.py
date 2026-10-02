"""Fallback extractor: pypdf (BSD, pure-Python, fast)."""
from __future__ import annotations

from pathlib import Path

from funnel.extraction.base import ExtractedPage, ExtractionResult


class PyPdfExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[ExtractedPage] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(ExtractedPage(page_no=i, text=text, char_count=len(text)))
        full = "\n\n".join(p.text for p in pages).strip()
        return ExtractionResult(source_file=str(path), pages=pages, full_text=full)
