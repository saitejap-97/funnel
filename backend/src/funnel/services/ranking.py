"""Rank profiles against a JD. LLM scores, code aggregates + sorts."""
from __future__ import annotations

from funnel.llm.client import LlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus
from funnel.models.ranking import CriterionScore, RankResult
from funnel.rubric import RUBRIC_VERSION, aggregate, build_rank_prompt, rank_json_schema


class RankingService:
    def __init__(self, llm: LlmClient, rubric_version: str = RUBRIC_VERSION) -> None:
        self._llm = llm
        self._rubric_version = rubric_version

    def rank(
        self, profiles: list[CandidateProfile], jd_text: str, limit: int = 20
    ) -> list[RankResult]:
        results: list[RankResult] = []
        for p in profiles:
            if p.profile_status != ProfileStatus.OK:
                continue
            summary = (
                f"{p.name} | skills: {', '.join(p.skills)} | {p.summary} | "
                + "; ".join(
                    f"{e.title}@{e.company} ({e.years}y): {e.summary}"
                    for e in p.experience
                )
            )
            system, user = build_rank_prompt(summary, jd_text)
            data = self._llm.complete_json(
                system=system, user=user, schema=rank_json_schema()
            )
            total, breakdown = aggregate(
                list(data.get("scores", [])), self._rubric_version
            )
            results.append(
                RankResult(
                    candidate_id=p.id,
                    total_100=total,
                    breakdown=[CriterionScore.model_validate(b)
                               for b in breakdown],
                    rationale=str(data.get("rationale", ""))[:280],
                    rubric_version=self._rubric_version,
                )
            )
        # Deterministic order: score desc, then skills_match, then
        # experience_relevance, then id (stable). Matches docs/RUBRIC.md.
        def _score(r: RankResult, key: str) -> float:
            return next(
                (b.score_0_10 for b in r.breakdown if b.criterion == key), 0.0
            )

        def sort_key(r: RankResult) -> tuple:
            return (
                -r.total_100,
                -_score(r, "skills_match"),
                -_score(r, "experience_relevance"),
                r.candidate_id,
            )

        return sorted(results, key=sort_key)[:limit]
