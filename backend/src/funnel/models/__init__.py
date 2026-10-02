"""Dumb data models. Pydantic only — no I/O, no business logic."""
from funnel.models.profile import (
    CandidateProfile,
    Education,
    Experience,
    ProfileStatus,
    ResumeRaw,
)
from funnel.models.ranking import CriterionScore, RankResult

__all__ = [
    "CandidateProfile",
    "CriterionScore",
    "Education",
    "Experience",
    "ProfileStatus",
    "RankResult",
    "ResumeRaw",
]
