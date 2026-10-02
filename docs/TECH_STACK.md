# Tech stack (decided, Phase 0)

## Backend: Python only

| Concern | Choice | Why |
|---|---|---|
| HTTP framework | **FastAPI + Uvicorn** | Native Pydantic validation (shared with LLM schemas), auto OpenAPI for the future frontend, async fan-out for LLM calls. Django is overkill (no ORM/admin needed); Flask needs more glue. |
| Data shapes | **Pydantic v2** | Single source of truth for LLM JSON-schema, request/response DTOs, and stored profiles. `models/` stays dumb (no I/O). |
| PDF text extraction | **pdfplumber (primary) + pypdf (fallback)** behind `PdfTextExtractor` Protocol | pdfplumber (MIT): best tables + char/bbox evidence citations. pypdf (BSD): pure-Python fast fallback. Rejected PyMuPDF as default (AGPL). Scanned PDFs detected by char threshold → flagged `needs_ocr`, no silent empty profiles. |
| LLM access | **OpenRouter, OpenAI-compatible, via `openai` python SDK** | One key, many models, `provider/model` strings, trivial swap to Azure/direct OpenAI via `base_url`. Default extraction model: `openai/gpt-4o-mini` (cheap, good JSON). Premium ranking option: `anthropic/claude-sonnet-4.5` or `openai/gpt-4o`. `temperature=0`, `response_format=json_schema`, Pydantic re-validation, 1 repair retry, exponential backoff. |
| Persistence (now) | **JSON file on disk** behind `CandidateRepository` Protocol | Matches "store the file on disc, update when new resumes added". Atomic writes + file lock. Swap for Postgres later without touching services. |
| Config | **env vars + `config.py`** (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `RESUME_DIR`, `STORE_PATH`, `RUBRIC_VERSION`) | No secrets in repo. `config.py` reads env only; `main.py` instantiates. |
| Tests | **pytest + FastAPI TestClient** | Per-layer: models / extraction (golden PDFs) / llm (mocked) / repository (tmpfs) / services (faked deps) / api (contract only). |

## Frontend: deferred (deliberate)

Only the REST contract is fixed now (`docs/API_DESIGN.md`): JSON over HTTP,
stable `id`/`score` shapes, no HTML from the backend. When we revisit, likely
candidates are Next.js or a minimal Vite+React SPA against the same OpenAPI —
decision reserved until backend scoring is validated by HR.

## Alternatives considered

- Direct OpenAI / Anthropic / Azure OpenAI: same client, one-line swap.
  Prototype on OpenRouter; production HR PII likely wants Azure (Entra, VNet,
  residency). See README security note.
- `httpx` raw calls: rejected — `openai` SDK already handles auth, retries,
  tool/schema plumbing for OpenRouter.
- OCR now (`pytesseract`/`ocrmypdf`): deferred; extractor flags `needs_ocr`
  instead of hallucinating.
