"""Env-only config. Reads environment, instantiates nothing.

Composition (clients, stores, app) lives in main.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    resume_dir: str = "../../data/resumes"
    store_path: str = "../../data/store.json"
    rubric_version: str = "v1"
    app_version: str = "0.1.0"


def load_settings() -> Settings:
    return Settings(
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        openrouter_model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        resume_dir=os.environ.get("RESUME_DIR", "../../data/resumes"),
        store_path=os.environ.get("STORE_PATH", "../../data/store.json"),
        rubric_version=os.environ.get("RUBRIC_VERSION", "v1"),
        app_version=os.environ.get("APP_VERSION", "0.1.0"),
    )
