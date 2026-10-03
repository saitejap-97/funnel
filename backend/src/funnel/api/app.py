"""FastAPI app factory. Thin handlers delegate to services."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from funnel.models.profile import CandidateProfile, ProfileStatus
from funnel.models.ranking import CriterionScore, RankResult
from funnel.repository.base import CandidateRepository, JobRepository
from funnel.services.ingestion import IngestionService
from funnel.services.ranking import RankingService


class RankRequest(BaseModel):
    jd_text: str = ""
    jd_id: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class IngestRequest(BaseModel):
    resume_dir: str | None = None
    jd_dir: str | None = None


def create_app(
    *,
    repository: CandidateRepository,
    ingestion: IngestionService,
    ranking: RankingService,
    app_version: str = "0.1.0",
    rubric_version: str = "v1",
    default_resume_dir: str = "data/resumes",
    default_jd_dir: str = "data/job_descriptions",
    jobs: JobRepository | None = None,
    cors_origins: tuple[str, ...] | list[str] = (),
) -> FastAPI:
    app = FastAPI(title="Funnel HR screening", version=app_version)
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": app_version,
            "rubric_version": rubric_version,
        }

    @app.get("/api/v1/candidates")
    def list_candidates(
        q: str = Query(default=""),
        tag: str = Query(default=""),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ):
        # NOTE: substring/tag filtering here is presentation-level only
        # (no scoring or mutation). Rich querying moves to services/ later.
        items = repository.list()
        if q:
            ql = q.lower()
            items = [p for p in items if _matches(p, ql)]
        if tag:
            tl = tag.lower()
            items = [p for p in items if any(tl == s.lower() for s in p.skills)]
        total = len(items)
        return {"items": [p.model_dump() for p in items[offset : offset + limit]],
                "total": total}

    @app.get("/api/v1/candidates/{candidate_id}")
    def get_candidate(candidate_id: str):
        profile = repository.get(candidate_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="candidate not found")
        return profile.model_dump()

    @app.post("/api/v1/ingest", status_code=202)
    def trigger_ingest(body: IngestRequest):
        # NOTE: synchronous scan for v1 (fast for local folders).
        # Returns 202 for forward-compat with a future async job queue;
        # response already contains the final summary.
        summary = ingestion.scan(
            body.resume_dir or default_resume_dir,
            body.jd_dir or default_jd_dir,
        )
        return {
            "scanned": summary.scanned,
            "ingested": summary.ingested,
            "needs_ocr": summary.needs_ocr,
            "failed": summary.failed,
            "jobs_scanned": summary.jobs_scanned,
            "jobs_ingested": summary.jobs_ingested,
            "jobs_failed": summary.jobs_failed,
            "errors": summary.errors,
        }

    @app.get("/api/v1/jobs")
    def list_jobs():
        if jobs is None:
            raise HTTPException(status_code=501, detail="job store not configured")
        return {"items": [j.model_dump() for j in jobs.list()]}

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str):
        if jobs is None:
            raise HTTPException(status_code=501, detail="job store not configured")
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job.model_dump()

    @app.post("/api/v1/rank")
    def rank(body: RankRequest):
        jd_text = body.jd_text
        if body.jd_id:
            if jobs is None:
                raise HTTPException(status_code=501, detail="job store not configured")
            job = jobs.get(body.jd_id)
            if job is None:
                raise HTTPException(status_code=404, detail="job not found")
            jd_text = job.full_text
        if not jd_text.strip():
            raise HTTPException(status_code=422, detail="jd_text or jd_id is required")
        items: list[RankResult] = ranking.rank(
            repository.list(), jd_text, limit=body.limit
        )
        return {
            "items": [r.model_dump() for r in items],
            "rubric_version": rubric_version,
        }

    return app


def _matches(profile: CandidateProfile, ql: str) -> bool:
    """Substring search across name, skills, tags, summary, and experience."""
    if ql in profile.name.lower():
        return True
    if ql in " ".join(profile.skills).lower():
        return True
    if ql in " ".join(profile.tags).lower():
        return True
    if ql in profile.summary.lower():
        return True
    return any(
        ql in e.title.lower() or ql in e.company.lower() or ql in e.summary.lower()
        for e in profile.experience
    )
