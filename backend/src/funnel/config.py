"""Env-only config. Reads environment, instantiates nothing.

Relative RESUME_DIR/STORE_PATH are anchored at the repo root (parent of
backend/), never at the process cwd — otherwise `uvicorn` vs `pytest` vs
scripts each resolve differently.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # .../backend
REPO_ROOT = BACKEND_DIR.parent  # .../funnel (repo root)

DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    resume_dir: str = "data/resumes"
    store_path: str = "data/store.json"
    jd_dir: str = "data/job_descriptions"
    jobs_path: str = "data/jobs.json"
    rubric_version: str = "v1"
    app_version: str = "0.1.0"
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS


def _resolve(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path)
    for base in (REPO_ROOT, BACKEND_DIR, Path.cwd()):
        candidate = (base / path).resolve()
        if candidate.exists():
            return str(candidate)
    return str((REPO_ROOT / path).resolve())


def load_settings() -> Settings:
    return Settings(
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        openrouter_model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        resume_dir=_resolve(os.environ.get("RESUME_DIR", "data/resumes")),
        store_path=_resolve(os.environ.get("STORE_PATH", "data/store.json")),
        jd_dir=_resolve(os.environ.get("JD_DIR", "data/job_descriptions")),
        jobs_path=_resolve(os.environ.get("JOBS_PATH", "data/jobs.json")),
        rubric_version=os.environ.get("RUBRIC_VERSION", "v1"),
        app_version=os.environ.get("APP_VERSION", "0.1.0"),
        cors_origins=tuple(
            o.strip()
            for o in os.environ.get("CORS_ORIGINS", "").split(",")
            if o.strip()
        )
        or DEFAULT_CORS_ORIGINS,
    )
