"""API contract tests only (status + shape, no business logic)."""
from fastapi.testclient import TestClient

from funnel.api.app import create_app
from funnel.llm.client import StubLlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.ingestion import IngestionService
from funnel.services.profiling import ProfilingService
from funnel.services.ranking import RankingService


def _client(tmp_path):
    store = JsonFileCandidateStore(tmp_path / "s.json")
    store.upsert(CandidateProfile(
        id="c1", name="Ann Rao", skills=["python", "fastapi"],
        source_file="a.pdf", file_hash="h1", summary="backend engineer",
        profile_status=ProfileStatus.OK))
    stub = StubLlmClient(payload={
        "scores": [
            {"criterion": "skills_match", "score_0_10": 8,
             "evidence": "fastapi", "confidence": 0.8},
            {"criterion": "experience_relevance", "score_0_10": 7,
             "evidence": "", "confidence": 0.6},
            {"criterion": "education_fit", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
            {"criterion": "impact_signals", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
            {"criterion": "growth_trajectory", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
        ],
        "rationale": "strong backend fit",
    })

    class FakeExtractor:
        def extract(self, path):
            from funnel.extraction.base import ExtractionResult
            return ExtractionResult(source_file=str(path), pages=[],
                                    full_text="")

    profiling = ProfilingService(stub)
    app = create_app(
        repository=store,
        ingestion=IngestionService(FakeExtractor(), profiling, store),
        ranking=RankingService(stub),
    )
    return TestClient(app)


def test_health_and_candidates(tmp_path):
    c = _client(tmp_path)
    assert c.get("/health").json()["status"] == "ok"
    body = c.get("/api/v1/candidates").json()
    assert body["total"] == 1
    assert c.get("/api/v1/candidates/c1").status_code == 200
    assert c.get("/api/v1/candidates/nope").status_code == 404
    assert c.get("/api/v1/candidates?q=ann").json()["total"] == 1
    assert c.get("/api/v1/candidates?tag=python").json()["total"] == 1


def test_rank_requires_jd(tmp_path):
    c = _client(tmp_path)
    assert c.post("/api/v1/rank", json={"jd_text": "  "}).status_code == 422
    body = c.post("/api/v1/rank",
                  json={"jd_text": "python backend"}).json()
    assert body["items"][0]["candidate_id"] == "c1"
    assert body["rubric_version"] == "v1"


def test_ingest_endpoint_reports_summary(tmp_path):
    c = _client(tmp_path)
    body = c.post("/api/v1/ingest", json={"resume_dir": str(tmp_path)}).json()
    assert body["scanned"] == 0
    assert {"scanned", "ingested", "needs_ocr", "failed", "errors"} <= set(body)
