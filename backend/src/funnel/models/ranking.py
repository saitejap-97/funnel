"""Dumb ranking data. Aggregation math lives in rubric/, not here."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    criterion: str
    score_0_10: float = Field(ge=0, le=10)
    weight: float = Field(ge=0, le=1)
    evidence: str = ""
    confidence: float = Field(default=0.5, ge=0, le=1)


class RankResult(BaseModel):
    candidate_id: str
    total_100: float = Field(ge=0, le=100)
    breakdown: list[CriterionScore] = Field(default_factory=list)
    rationale: str = ""
    rubric_version: str = "v1"
