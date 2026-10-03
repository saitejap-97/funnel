"""Persisted rank cache: per-job sorted results + profile hashes.

Match views serve this stale data instantly; only stale/missing
(candidate, job) pairs cost LLM calls. Same atomic-write pattern
as the other JSON stores. Swap for DB later.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from funnel.models.ranking import RankResult


class CachedRanking(BaseModel):
    job_id: str
    results: list[RankResult] = Field(default_factory=list)
    profile_hashes: dict[str, str] = Field(default_factory=dict)
    rubric_version: str = "v1"
    computed_at: str = ""


class EvaluationRepository(Protocol):
    def get(self, job_id: str) -> CachedRanking | None: ...
    def put(self, cached: CachedRanking) -> None: ...


class JsonFileEvaluationStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("{}")

    def _read_all(self) -> dict[str, CachedRanking]:
        try:
            data = json.loads(self._path.read_text() or "{}")
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        out = {}
        for job_id, item in data.items():
            try:
                out[job_id] = CachedRanking.model_validate(item)
            except Exception:
                continue
        return out

    def get(self, job_id: str) -> CachedRanking | None:
        return self._read_all().get(job_id)

    def put(self, cached: CachedRanking) -> None:
        all_cached = self._read_all()
        cached.computed_at = datetime.now(timezone.utc).isoformat()
        all_cached[cached.job_id] = cached
        payload = json.dumps(
            {k: v.model_dump() for k, v in all_cached.items()}, indent=2
        )
        fd, tmp = tempfile.mkstemp(dir=str(self._path.parent))
        try:
            with os.fdopen(fd, "w") as f:
                f.write(payload)
            os.replace(tmp, self._path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
