"""Services with faked deps: profiling, ranking determinism, ingest idempotency."""
from funnel.llm.client import StubLlmClient
from funnel.models.profile import CandidateProfile, ProfileStatus, ResumeRaw
from funnel.repository.job_store import JsonFileJobStore
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.ingestion import (
    IngestionService,
    job_title_from_filename,
)
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


def test_profiling_normalizes_strict_mode_sentinels():
    """Strict schemas use ''/0 for unknown email/year; service maps to None."""
    stub = StubLlmClient(payload={"name": "John", "email": "",
                                  "skills": ["python"], "experience": [],
                                  "education": [{"degree": "BS", "school": "X",
                                                 "year": 0}],
                                  "summary": "dev", "tags": []})
    p = ProfilingService(stub).build_profile(
        ResumeRaw(source_file="s.pdf", file_hash="h",
                  full_text="John Python dev with many years of experience"))
    assert p.profile_status == ProfileStatus.OK
    assert p.email is None
    assert p.education[0].year is None


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


def test_job_title_from_filename(tmp_path):
    assert job_title_from_filename(
        tmp_path / "01_jd_senior_backend_engineer_payments.pdf"
    ) == "Senior Backend Engineer Payments"
    assert job_title_from_filename(tmp_path / "jd_data_scientist.pdf") == "Data Scientist"


def test_ingest_scans_job_descriptions(tmp_path):
    from funnel.extraction.base import ExtractedPage, ExtractionResult

    jd_dir = tmp_path / "jds"
    jd_dir.mkdir()
    (jd_dir / "01_jd_backend_engineer.pdf").write_bytes(b"%PDF fake jd")

    class FakeExtractor:
        def extract(self, path):
            text = "Senior backend engineer needed: Python, Kubernetes, Postgres. " * 3
            return ExtractionResult(
                source_file=str(path),
                pages=[ExtractedPage(page_no=1, text=text, char_count=len(text))],
                full_text=text,
            )

    stub = StubLlmClient(payload={"name": "N", "skills": [], "experience": [],
                                  "education": [], "summary": "", "tags": []})
    store = JsonFileCandidateStore(tmp_path / "store.json")
    jobs = JsonFileJobStore(tmp_path / "jobs.json")
    svc = IngestionService(FakeExtractor(), ProfilingService(stub), store, jobs)
    # tmp_path has no resume pdfs (only .pdf is under jds/), jd scan runs.
    summary = svc.scan(tmp_path, jd_dir)
    assert (summary.jobs_scanned, summary.jobs_ingested) == (1, 1)
    assert jobs.list()[0].title == "Backend Engineer"
    assert "Python" in jobs.list()[0].full_text
    # Idempotent re-scan.
    summary2 = svc.scan(tmp_path, jd_dir)
    assert len(jobs.list()) == 1
    assert (summary2.jobs_scanned, summary2.jobs_ingested) == (1, 1)


def test_same_text_different_bytes_share_profile_id():
    """Re-exported PDFs (same text, different bytes) dedupe to one profile."""
    from funnel.services.ingestion import content_hash

    text = "Jane Doe, Python engineer with many years of backend experience."
    stub = StubLlmClient(payload={"name": "Jane", "skills": ["python"],
                                  "experience": [], "education": [],
                                  "summary": "eng", "tags": []})
    svc = ProfilingService(stub)
    a = svc.build_profile(ResumeRaw(source_file="a.pdf", file_hash="bytes1",
                                    full_text=text,
                                    content_hash=content_hash(text)))
    b = svc.build_profile(ResumeRaw(source_file="b.pdf", file_hash="bytes2",
                                    full_text=text + " ",
                                    content_hash=content_hash(text + " ")))
    assert a.id == b.id
    assert a.profile_status == ProfileStatus.OK


def test_empty_text_profiles_do_not_collide():
    svc = ProfilingService(StubLlmClient(payload={}))
    a = svc.build_profile(ResumeRaw(source_file="a.pdf", file_hash="h1",
                                    full_text="",
                                    content_hash="e3b0c44298fc1c149"))
    b = svc.build_profile(ResumeRaw(source_file="b.pdf", file_hash="h2",
                                    full_text="  ",
                                    content_hash="e3b0c44298fc1c149"))
    assert a.id != b.id
    assert a.profile_status == ProfileStatus.NEEDS_OCR


def _rank_stub():
    return StubLlmClient(payload={
        "scores": [
            {"criterion": "skills_match", "score_0_10": 8,
             "evidence": "e", "confidence": 0.8},
            {"criterion": "experience_relevance", "score_0_10": 7,
             "evidence": "", "confidence": 0.5},
            {"criterion": "education_fit", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
            {"criterion": "impact_signals", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
            {"criterion": "growth_trajectory", "score_0_10": 6,
             "evidence": "", "confidence": 0.5},
        ],
        "rationale": "fit",
    })


def _eval_setup(tmp_path, stub):
    from funnel.models.job import JobDescription
    from funnel.services.evaluation import EvaluationService
    from funnel.repository.evaluations import JsonFileEvaluationStore

    store = JsonFileCandidateStore(tmp_path / "s.json")
    jobs = JsonFileJobStore(tmp_path / "j.json")
    evals = JsonFileEvaluationStore(tmp_path / "e.json")
    jobs.upsert(JobDescription(id="j1", title="Backend", source_file="jd.pdf",
                               file_hash="h", full_text="python backend"))
    return store, EvaluationService(stub, store, jobs, evals)


def test_ensure_ranked_caches_second_call(tmp_path):
    stub = _rank_stub()
    store, svc = _eval_setup(tmp_path, stub)
    store.upsert(_profile("c1", "Ann"))
    first, fresh1 = svc.ensure_ranked("j1")
    assert fresh1 is False
    assert len(stub.calls) == 1
    second, fresh2 = svc.ensure_ranked("j1")
    assert fresh2 is True  # zero LLM calls
    assert len(stub.calls) == 1
    assert [r.candidate_id for r in second] == [r.candidate_id for r in first]


def test_ensure_ranked_only_rescores_changed(tmp_path):
    stub = _rank_stub()
    store, svc = _eval_setup(tmp_path, stub)
    store.upsert(_profile("c1", "Ann"))
    svc.ensure_ranked("j1")
    assert len(stub.calls) == 1
    # New resume: only the new pair costs an LLM call.
    new = _profile("c2", "Bob")
    store.upsert(new)
    results, fresh = svc.ensure_ranked("j1")
    assert fresh is False
    assert len(stub.calls) == 2
    assert {r.candidate_id for r in results} == {"c1", "c2"}
    # Updated resume (new content hash): rescores just that pair.
    changed = _profile("c1", "Ann")
    changed.content_hash = "different-content"
    store.upsert(changed)
    svc.ensure_ranked("j1")
    assert len(stub.calls) == 3


def test_ensure_ranked_unknown_job(tmp_path):
    import pytest

    _, svc = _eval_setup(tmp_path, _rank_stub())
    with pytest.raises(KeyError):
        svc.ensure_ranked("nope")
