"""Persistence behind a Protocol. Services never touch JSON directly."""
from funnel.repository.base import CandidateRepository, JobRepository
from funnel.repository.job_store import JsonFileJobStore
from funnel.repository.json_store import JsonFileCandidateStore

__all__ = [
    "CandidateRepository",
    "JobRepository",
    "JsonFileCandidateStore",
    "JsonFileJobStore",
]
