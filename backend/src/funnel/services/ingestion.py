"""Folder scan → extract → profile → store. Idempotent on file hash."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from funnel.extraction.base import PdfTextExtractor
from funnel.models.job import JobDescription
from funnel.models.profile import ProfileStatus, ResumeRaw
from funnel.repository.base import CandidateRepository, JobRepository
from funnel.services.profiling import ProfilingService

MIN_CHARS_OK = 50

_FILENAME_JUNK = re.compile(r"^\d+_jd_", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Collapse all whitespace — byte-different re-exports compare equal."""
    return " ".join(text.split())


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode()).hexdigest()


@dataclass
class IngestionSummary:
    scanned: int = 0
    ingested: int = 0  # ProfileStatus.OK
    needs_ocr: int = 0  # stored but flagged NEEDS_OCR — not silently "ingested"
    failed: int = 0
    jobs_scanned: int = 0
    jobs_ingested: int = 0
    jobs_failed: int = 0
    errors: list[str] = field(default_factory=list)


def job_title_from_filename(path: Path) -> str:
    """01_jd_senior_backend_engineer_payments.pdf → Senior Backend Engineer Payments."""
    stem = _FILENAME_JUNK.sub("", path.stem)
    stem = stem.removeprefix("jd_")
    return stem.replace("_", " ").replace("-", " ").title()


class IngestionService:
    def __init__(
        self,
        extractor: PdfTextExtractor,
        profiling: ProfilingService,
        repository: CandidateRepository,
        jobs: JobRepository | None = None,
    ) -> None:
        self._extractor = extractor
        self._profiling = profiling
        self._repository = repository
        self._jobs = jobs

    def scan(self, resume_dir: str | Path, jd_dir: str | Path | None = None) -> IngestionSummary:
        summary = IngestionSummary()
        directory = Path(resume_dir)
        if not directory.exists():
            summary.errors.append(f"resume_dir not found: {directory}")
            return summary
        for pdf in sorted(directory.rglob("*.pdf")):
            summary.scanned += 1
            try:
                result = self._extractor.extract(pdf)
                blob = pdf.read_bytes()
                raw = ResumeRaw(
                    source_file=str(pdf),
                    file_hash=hashlib.sha256(blob).hexdigest(),
                    full_text=result.full_text,
                    needs_ocr=len(result.full_text.strip()) < MIN_CHARS_OK,
                    content_hash=content_hash(result.full_text),
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
        if jd_dir is not None and self._jobs is not None:
            self._scan_jobs(Path(jd_dir), summary)
        return summary

    def _scan_jobs(self, directory: Path, summary: IngestionSummary) -> None:
        if not directory.exists():
            summary.errors.append(f"jd_dir not found: {directory}")
            return
        for pdf in sorted(directory.rglob("*.pdf")):
            summary.jobs_scanned += 1
            try:
                result = self._extractor.extract(pdf)
                blob = pdf.read_bytes()
                file_hash = hashlib.sha256(blob).hexdigest()
                self._jobs.upsert(
                    JobDescription(
                        id=hashlib.sha1(file_hash.encode()).hexdigest()[:16],
                        title=job_title_from_filename(pdf),
                        source_file=str(pdf),
                        file_hash=file_hash,
                        full_text=result.full_text,
                    )
                )
                summary.jobs_ingested += 1
            except Exception as exc:
                summary.jobs_failed += 1
                summary.errors.append(f"{pdf.name}: {exc}")
