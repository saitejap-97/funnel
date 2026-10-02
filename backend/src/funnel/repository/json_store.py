"""JSON-file store: atomic writes, tolerant reads. Swap for DB later."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from funnel.models.profile import CandidateProfile


class JsonFileCandidateStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_all([])

    def _read_all(self) -> list[CandidateProfile]:
        try:
            data = json.loads(self._path.read_text() or "[]")
        except (json.JSONDecodeError, FileNotFoundError):
            return []  # corrupt/missing → start empty, never crash ingest
        profiles = []
        for item in data:
            try:
                profiles.append(CandidateProfile.model_validate(item))
            except Exception:
                continue  # skip bad rows, keep good ones
        return profiles

    def _write_all(self, profiles: list[CandidateProfile]) -> None:
        payload = json.dumps([p.model_dump() for p in profiles], indent=2)
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

    def upsert(self, profile: CandidateProfile) -> None:
        profiles = [p for p in self._read_all() if p.id != profile.id]
        profiles.append(profile)
        self._write_all(profiles)

    def get(self, candidate_id: str) -> CandidateProfile | None:
        for p in self._read_all():
            if p.id == candidate_id:
                return p
        return None

    def list(self) -> list[CandidateProfile]:
        return self._read_all()
