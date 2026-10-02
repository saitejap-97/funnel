"""Data models package for Funnel HR System."""

from .resume import (
    ContactInfo,
    Experience,
    Education,
    Skill,
    Candidate,
    Resume,
    ResumeCreate,
    ResumeResponse,
)
from .job import (
    Requirement,
    Rubric,
    JobDescription,
    JobCreate,
    JobResponse,
)
from .evaluation import (
    RequirementScore,
    EvaluationResult,
    EvaluationCreate,
    EvaluationResponse,
    RankedCandidate,
)
from .api import (
    UploadResponse,
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    # Resume models
    "ContactInfo",
    "Experience",
    "Education",
    "Skill",
    "Candidate",
    "Resume",
    "ResumeCreate",
    "ResumeResponse",
    # Job models
    "Requirement",
    "Rubric",
    "JobDescription",
    "JobCreate",
    "JobResponse",
    # Evaluation models
    "RequirementScore",
    "EvaluationResult",
    "EvaluationCreate",
    "EvaluationResponse",
    "RankedCandidate",
    # API models
    "UploadResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
]