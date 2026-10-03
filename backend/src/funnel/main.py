"""Composition root. Only place that instantiates clients/stores/services."""
from __future__ import annotations

from funnel.api.app import create_app
from funnel.config import load_settings
from funnel.extraction.factory import build_extractor
from funnel.llm.client import OpenRouterClient, StubLlmClient
from funnel.repository.evaluations import JsonFileEvaluationStore
from funnel.repository.job_store import JsonFileJobStore
from funnel.repository.json_store import JsonFileCandidateStore
from funnel.services.evaluation import EvaluationService
from funnel.services.ingestion import IngestionService
from funnel.services.profiling import ProfilingService
from funnel.services.ranking import RankingService

_settings = load_settings()
_store = JsonFileCandidateStore(_settings.store_path)
_job_store = JsonFileJobStore(_settings.jobs_path)
_eval_store = JsonFileEvaluationStore(_settings.evals_path)
_extractor = build_extractor()

if _settings.openrouter_api_key:
    _llm: OpenRouterClient | StubLlmClient = OpenRouterClient(
        api_key=_settings.openrouter_api_key,
        base_url=_settings.openrouter_base_url,
        model=_settings.openrouter_model,
    )
else:  # offline / no key: stub returns empty-but-valid shapes, never crashes
    _llm = StubLlmClient(
        payload={
            "name": "",
            "skills": [],
            "experience": [],
            "education": [],
            "summary": "",
            "tags": [],
            "scores": [],
            "rationale": "",
        }
    )

_profiling = ProfilingService(_llm)
_ingestion = IngestionService(_extractor, _profiling, _store, _job_store)
_ranking = RankingService(_llm, rubric_version=_settings.rubric_version)
_evaluation = EvaluationService(
    _llm, _store, _job_store, _eval_store,
    rubric_version=_settings.rubric_version,
)

app = create_app(
    repository=_store,
    ingestion=_ingestion,
    ranking=_ranking,
    app_version=_settings.app_version,
    rubric_version=_settings.rubric_version,
    default_resume_dir=_settings.resume_dir,
    default_jd_dir=_settings.jd_dir,
    jobs=_job_store,
    evaluation=_evaluation,
    cors_origins=_settings.cors_origins,
)
