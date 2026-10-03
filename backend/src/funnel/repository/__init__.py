"""Persistence behind a Protocol. Services never touch JSON directly."""
from funnel.repository.base import CandidateRepository, JobRepository
from funnel.repository.evaluations import (
    CachedRanking,
    EvaluationRepository,
    JsonFileEvaluationStore,
)
from funnel.repository.job_store import JsonFileJobStore
from funnel.repository.json_store import JsonFileCandidateStore

__all__ = [
    "CachedRanking",
    "CandidateRepository",
    "EvaluationRepository",
    "JobRepository",
    "JsonFileCandidateStore",
    "JsonFileEvaluationStore",
    "JsonFileJobStore",
]
