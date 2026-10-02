"""Services with faked deps: profiling, ranking determinism, ingest idempotency."""
from funnel.llm.client import StubLlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus, ResumeRaw
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.ingestion import IngestionService
from funnel.services.profiling import ProfilingService
from funnel.services.ranking import RankingService


def _profile(cid="c1", name="Ann", skills=None):
    return CandidateProfile(
        id=cid, name=name, skills=skills or ["python"],
        source_file="a.pdf", file_hash="h" + cid,
        summary="backend engineer",
        profile_status=ProfileStatus.OK,
    )


def test_profiling_needs_ocr_short_circuits_llm():
    stub = StubLlmClient(payload={"name": "X", "skills": [],
                                  "experience": [], "education": [],
                                  "summary": "", "tags": []})
    svc = ProfilingService(stub)
    p = svc.build_profile(ResumeRaw(source_file="s.pdf", file_hash="h",
                                    full_text="  ", needs_ocr=True))
    assert p.profile_status == ProfileStatus.NEEDS_OCR
    assert stub.calls == []


def test_profiling_failed_on_invalid_llm_output():
    stub = StubLlmClient(payload={"name": "John", "skills": "not-a-list",
                                  "experience": [], "education": [],
                                  "summary": "x", "tags": []})
    svc = ProfilingService(stub)
    p = svc.build_profile(ResumeRaw(source_file="s.pdf", file_hash="h",
                                    full_text="John Python 5y"))
    assert p.profile_status == ProfileStatus.FAILED


def test_ranking_sorts_by_weighted_total():
    def llm_for(score):
        return StubLlmClient(payload={
            "scores": [
                {"criterion": "skills_match", "score_0_10": score,
                 "evidence": "e", "confidence": 0.9},
                {"criterion": "experience_relevance", "score_0_10": 5,
                 "evidence": "", "confidence": 0.5},
                {"criterion": "education_fit", "score_0_10": 5,
                 "evidence": "", "confidence": 0.5},
                {"criterion": "impact_signals", "score_0_10": 5,
                 "evidence": "", "confidence": 0.5},
                {"criterion": "growth_trajectory", "score_0_10": 5,
                 "evidence": "", "confidence": 0.5},
            ],
            "rationale": "ok",
        })

    # per-candidate LLM: route by name via a tiny dispatcher
    class Router:
        def complete_json(self, *, system, user, schema):
            score = 9.0 if "Ann" in user else 2.0
            return llm_for(score).complete_json(
                system=system, user=user, schema=schema)

    svc = RankingService(Router())  # type: ignore[arg-type]
    ranked = svc.rank([_profile("c2", "Bob"), _profile("c1", "Ann")],
                      "python backend", limit=10)
    assert [r.candidate_id for r in ranked] == ["c1", "c2"]
    assert ranked[0].total_100 > ranked[1].total_100


def test_ingest_idempotent(tmp_path):
    pdf = tmp_path / "r.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    class FakeExtractor:
        def extract(self, path):
            from funnel.extraction.base import ExtractedPage, ExtractionResult
            text = ("John Python dev 5 years building backend APIs with "
                    "FastAPI and Postgres")
            return ExtractionResult(
                source_file=str(path),
                pages=[ExtractedPage(page_no=1, text=text,
                                     char_count=len(text))],
                full_text=text,
            )

    stub = StubLlmClient(payload={"name": "John", "skills": ["python"],
                                  "experience": [], "education": [],
                                  "summary": "dev", "tags": []})
    store = JsonFileCandidateStore(tmp_path / "store.json")
    svc = IngestionService(FakeExtractor(), ProfilingService(stub), store)
    s1 = svc.scan(tmp_path)
    s2 = svc.scan(tmp_path)  # same file hash → upsert, not duplicate
    assert (s1.scanned, s1.ingested) == (1, 1)
    assert (s2.scanned, s2.ingested) == (1, 1)
    assert len(store.list()) == 1
