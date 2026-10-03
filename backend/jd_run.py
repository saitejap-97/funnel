"""Live JD check: ingest resumes + JDs (dirs via env), rank JD #1 by id.

Usage (from backend/):
    set -a; source .env; set +a
    RESUME_DIR=<resumes> JD_DIR=<jds> PYTHONPATH=src python -u jd_run.py
"""
from funnel.config import load_settings
from funnel.extraction.factory import build_extractor
from funnel.llm.client import OpenRouterClient
from funnel.repository.job_store import JsonFileJobStore
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.ingestion import IngestionService
from funnel.services.profiling import ProfilingService
from funnel.services.ranking import RankingService


def main() -> None:
    s = load_settings()
    llm = OpenRouterClient(
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        model=s.openrouter_model,
    )
    store = JsonFileCandidateStore(s.store_path)
    jobs = JsonFileJobStore(s.jobs_path)
    summary = IngestionService(
        build_extractor(), ProfilingService(llm), store, jobs
    ).scan(s.resume_dir, s.jd_dir)
    print(
        f"ingest: resumes {summary.ingested}/{summary.scanned} "
        f"jobs {summary.jobs_ingested}/{summary.jobs_scanned} "
        f"errors={summary.errors}",
        flush=True,
    )
    for j in jobs.list():
        print(f"  JD: {j.title} ({len(j.full_text)} chars)", flush=True)
    backend_jd = next(
        (j for j in jobs.list() if "Backend Engineer" in j.title), None
    )
    if backend_jd is None:
        print("backend JD not found, skipping rank", flush=True)
        return
    ranked = RankingService(llm, rubric_version=s.rubric_version).rank(
        store.list(), backend_jd.full_text, limit=10
    )
    print(f"rank by jd_id={backend_jd.id} ({backend_jd.title}):", flush=True)
    for r in ranked:
        p = store.get(r.candidate_id)
        print(f"  {r.total_100:5.1f}  {p.name}", flush=True)


if __name__ == "__main__":
    main()
