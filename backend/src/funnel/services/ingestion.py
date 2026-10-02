"""Folder scan → extract → profile → store. Idempotent on file hash."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from funnel.extraction.base import PdfTextExtractor
from funnel.models.profile import ProfileStatus, ResumeRaw
from funnel.repository.base import CandidateRepository
from funnel.services.profiling import ProfilingService

MIN_CHARS_OK = 50


@dataclass
class IngestionSummary:
    scanned: int = 0
    ingested: int = 0  # ProfileStatus.OK
    needs_ocr: int = 0  # stored but flagged NEEDS_OCR — not silently "ingested"
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class IngestionService:
    def __init__(
        self,
        extractor: PdfTextExtractor,
        profiling: ProfilingService,
        repository: CandidateRepository,
    ) -> None:
        self._extractor = extractor
        self._profiling = profiling
        self._repository = repository

    def scan(self, resume_dir: str | Path) -> IngestionSummary:
        summary = IngestionSummary()
        directory = Path(resume_dir)
        if not directory.exists():
            summary.errors.append(f"resume_dir not found: {directory}")
            return summary
        for pdf in sorted(directory.glob("*.pdf")):
            summary.scanned += 1
            try:
                result = self._extractor.extract(pdf)
                blob = pdf.read_bytes()
                raw = ResumeRaw(
                    source_file=str(pdf),
                    file_hash=hashlib.sha256(blob).hexdigest(),
                    full_text=result.full_text,
                    needs_ocr=len(result.full_text.strip()) < MIN_CHARS_OK,
                )
                profile = self._profiling.build_profile(raw)
                self._repository.upsert(profile)
                if profile.profile_status == ProfileStatus.OK:
                    summary.ingested += 1
                elif profile.profile_status == ProfileStatus.NEEDS_OCR:
                    summary.needs_ocr += 1
                else:
                    summary.failed += 1
            except Exception as exc:
                summary.failed += 1
                summary.errors.append(f"{pdf.name}: {exc}")
        return summary
