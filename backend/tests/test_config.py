"""Config: relative paths anchor at repo root, independent of cwd."""
import os
from pathlib import Path

from funnel.config import REPO_ROOT, load_settings


def test_resume_dir_resolves_to_existing_folder():
    s = load_settings()
    assert Path(s.resume_dir).is_absolute()
    assert Path(s.resume_dir).name == "resumes"


def test_explicit_relative_paths_anchor_at_repo_root(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUME_DIR", "data/resumes")
    monkeypatch.setenv("STORE_PATH", "data/store.json")
    s = load_settings()
    assert Path(s.resume_dir).parent == REPO_ROOT / "data"
    assert Path(s.store_path).parent == REPO_ROOT / "data"


def test_absolute_paths_pass_through(monkeypatch, tmp_path):
    monkeypatch.setenv("RESUME_DIR", str(tmp_path))
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.json"))
    s = load_settings()
    assert s.resume_dir == str(tmp_path)
    assert os.path.isabs(s.store_path)
