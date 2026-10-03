"""JSON-file job store. Same atomic-write pattern as candidates."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from funnel.models.job import JobDescription


class JsonFileJobStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_all([])

    def _read_all(self) -> list[JobDescription]:
        try:
            data = json.loads(self._path.read_text() or "[]")
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        jobs = []
        for item in data:
            try:
                jobs.append(JobDescription.model_validate(item))
            except Exception:
                continue
        return jobs

    def _write_all(self, jobs: list[JobDescription]) -> None:
        payload = json.dumps([j.model_dump() for j in jobs], indent=2)
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

    def upsert(self, job: JobDescription) -> None:
        jobs = [j for j in self._read_all() if j.id != job.id]
        jobs.append(job)
        self._write_all(jobs)

    def get(self, job_id: str) -> JobDescription | None:
        for j in self._read_all():
            if j.id == job_id:
                return j
        return None

    def list(self) -> list[JobDescription]:
        return sorted(self._read_all(), key=lambda j: j.title)
