"""Stale-while-revalidate ranking: serve cached scores, recompute only
what changed (new/updated resume, new JD, first view).

The frontend match view is a pure data read after warmup — zero LLM calls.
"""
from __future__ import annotations

from funnel.llm.client import LlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus
from funnel.models.ranking import RankResult
from funnel.repository.base import CandidateRepository, JobRepository
from funnel.repository.evaluations import CachedRanking, EvaluationRepository
from funnel.rubric import RUBRIC_VERSION
from funnel.services.ranking import RankingService, sort_ranked


class EvaluationService:
    def __init__(
        self,
        llm: LlmClient,
        candidates: CandidateRepository,
        jobs: JobRepository,
        evaluations: EvaluationRepository,
        rubric_version: str = RUBRIC_VERSION,
    ) -> None:
        self._ranking = RankingService(llm, rubric_version=rubric_version)
        self._candidates = candidates
        self._jobs = jobs
        self._evaluations = evaluations
        self._rubric_version = rubric_version

    def ensure_ranked(self, job_id: str, limit: int = 20) -> tuple[list[RankResult], bool]:
        """Return (results, fresh) — fresh=True means every pair was cached,
        i.e. zero LLM calls were made."""
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        profiles = [
            p for p in self._candidates.list()
            if p.profile_status == ProfileStatus.OK
        ]
        cached = self._evaluations.get(job_id)
        valid = self._valid_cached(cached, profiles) if cached else {}
        stale = [p for p in profiles if p.id not in valid]
        if not stale and cached is not None:
            return sort_ranked(list(cached.results))[:limit], True
        fresh = self._ranking.rank(stale, job.full_text, limit=len(stale) or 1)
        merged = list(valid.values()) + fresh
        self._evaluations.put(
            CachedRanking(
                job_id=job_id,
                results=sort_ranked(merged),
                profile_hashes={p.id: _identity(p) for p in profiles},
                rubric_version=self._rubric_version,
            )
        )
        return sort_ranked(merged)[:limit], False

    def _valid_cached(
        self, cached: CachedRanking, profiles: list[CandidateProfile]
    ) -> dict[str, RankResult]:
        by_id = {r.candidate_id: r for r in cached.results}
        valid = {}
        for p in profiles:
            if cached.profile_hashes.get(p.id) == _identity(p) and p.id in by_id:
                valid[p.id] = by_id[p.id]
        return valid


def _identity(profile: CandidateProfile) -> str:
    """Content hash when known (self-heals old stores on first recompute),
    else the byte hash."""
    return profile.content_hash or profile.file_hash
