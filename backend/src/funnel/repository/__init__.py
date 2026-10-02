"""Persistence behind a Protocol. Services never touch JSON directly."""
from funnel.repository.base import CandidateRepository
from funnel.repository.json_store import JsonFileCandidateStore

__all__ = ["CandidateRepository", "JsonFileCandidateStore"]
