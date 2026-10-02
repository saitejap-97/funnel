"""Turn ResumeRaw into a validated CandidateProfile via the LLM."""
from __future__ import annotations

import hashlib

from funnel.llm.client import LlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus
from funnel.models.profile import ResumeRaw
from funnel.rubric import build_profile_prompt, profile_json_schema


class ProfilingService:
    def __init__(self, llm: LlmClient) -> None:
        self._llm = llm

    def build_profile(self, raw: ResumeRaw) -> CandidateProfile:
        if raw.needs_ocr or not raw.full_text.strip():
            return CandidateProfile(
                id=_stable_id(raw.file_hash),
                name="",
                source_file=raw.source_file,
                file_hash=raw.file_hash,
                profile_status=ProfileStatus.NEEDS_OCR,
                summary="Extraction empty — likely scanned PDF, needs OCR.",
            )
        system, user = build_profile_prompt(raw.full_text)
        data = self._llm.complete_json(
            system=system, user=user, schema=profile_json_schema()
        )
        try:
            return CandidateProfile.model_validate(
                {
                    **data,
                    "id": _stable_id(raw.file_hash),
                    "source_file": raw.source_file,
                    "file_hash": raw.file_hash,
                    "profile_status": ProfileStatus.OK,
                }
            )
        except Exception as exc:
            return CandidateProfile(
                id=_stable_id(raw.file_hash),
                name="",
                source_file=raw.source_file,
                file_hash=raw.file_hash,
                profile_status=ProfileStatus.FAILED,
                summary=f"LLM output failed validation: {exc}",
            )


def _stable_id(file_hash: str) -> str:
    return hashlib.sha1(file_hash.encode()).hexdigest()[:16]
