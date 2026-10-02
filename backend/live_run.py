"""Live end-to-end: ingest all resumes with the real LLM, then rank.

Usage (from backend/):
    set -a; source .env; set +a
    PYTHONPATH=src python -u live_run.py

Writes progress to stdout; safe to re-run (ingest is idempotent on file hash).
"""
from funnel.config import load_settings
from funnel.extraction.factory import build_extractor
from funnel.llm.client import OpenRouterClient
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.ingestion import IngestionService
from funnel.services.profiling import ProfilingService
from funnel.services.ranking import RankingService

JD = (
    "Senior backend engineer: Go or Python, Kubernetes, Postgres, "
    "high-traffic distributed systems, on-call ownership."
)


def main() -> None:
    s = load_settings()
    print(f"resume_dir: {s.resume_dir}", flush=True)
    print(f"store: {s.store_path}", flush=True)
    llm = OpenRouterClient(
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        model=s.openrouter_model,
    )
    store = JsonFileCandidateStore(s.store_path)
    summary = IngestionService(build_extractor(), ProfilingService(llm), store).scan(
        s.resume_dir
    )
    print(
        f"ingest: scanned={summary.scanned} ingested={summary.ingested} "
        f"needs_ocr={summary.needs_ocr} failed={summary.failed} "
        f"errors={summary.errors}",
        flush=True,
    )
    ranked = RankingService(llm, rubric_version=s.rubric_version).rank(
        store.list(), JD, limit=10
    )
    print(f"JD: {JD}", flush=True)
    for r in ranked:
        p = store.get(r.candidate_id)
        print(f"{r.total_100:5.1f}  {p.name:25s} {r.rationale[:95]}", flush=True)


if __name__ == "__main__":
    main()
