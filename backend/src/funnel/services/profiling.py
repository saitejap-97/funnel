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
        # Identity = normalized-text hash (same resume, re-exported PDF → same
        # profile). Empty/OCR text would collide, so those fall back to bytes.
        identity = (
            raw.content_hash
            if (raw.content_hash and not raw.needs_ocr and raw.full_text.strip())
            else raw.file_hash
        )
        if raw.needs_ocr or not raw.full_text.strip():
            return CandidateProfile(
                id=_stable_id(identity),
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
        # Strict-mode schemas can't express null unions, so the schema uses
        # ""/0 sentinels for unknown email/year — normalize back to None here.
        if not data.get("email"):
            data["email"] = None
        for entry in data.get("education", []):
            if isinstance(entry, dict) and not entry.get("year"):
                entry["year"] = None
        try:
            return CandidateProfile.model_validate(
                {
                    **data,
                    "id": _stable_id(identity),
                    "source_file": raw.source_file,
                    "file_hash": raw.file_hash,
                    "profile_status": ProfileStatus.OK,
                    "content_hash": raw.content_hash,
                }
            )
        except Exception as exc:
            return CandidateProfile(
                id=_stable_id(identity),
                name="",
                source_file=raw.source_file,
                file_hash=raw.file_hash,
                profile_status=ProfileStatus.FAILED,
                summary=f"LLM output failed validation: {exc}",
            )


def _stable_id(file_hash: str) -> str:
    return hashlib.sha1(file_hash.encode()).hexdigest()[:16]
