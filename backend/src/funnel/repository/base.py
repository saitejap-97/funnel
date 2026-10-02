"""Repository contract."""
from __future__ import annotations

from typing import Protocol

from funnel.models.profile import CandidateProfile


class CandidateRepository(Protocol):
    def upsert(self, profile: CandidateProfile) -> None: ...
    def get(self, candidate_id: str) -> CandidateProfile | None: ...
    def list(self) -> list[CandidateProfile]: ...
