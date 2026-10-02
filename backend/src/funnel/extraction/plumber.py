"""Primary extractor: pdfplumber (MIT, tables + bboxes). Fallback-safe."""
from __future__ import annotations

from pathlib import Path

from funnel.extraction.base import ExtractedPage, ExtractionResult


class PlumberExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        import pdfplumber  # local import: keeps base import-light for tests

        pages: list[ExtractedPage] = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(
                    ExtractedPage(page_no=i, text=text, char_count=len(text))
                )
        full = "\n\n".join(p.text for p in pages).strip()
        return ExtractionResult(source_file=str(path), pages=pages, full_text=full)
