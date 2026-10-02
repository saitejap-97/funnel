# Funnel — internal HR resume screening & ranking

Internal-only fullstack app: drop candidate PDFs in a local folder,
extract text, ask an LLM (via OpenRouter) for structured profiles,
score them against a versioned rubric + job description, and serve
results over a small REST API for a future frontend.

> Status: **design + modular skeleton (Phase 0)**. Backend is Python-only
> (FastAPI + Pydantic v2). Frontend is intentionally deferred — see
> `docs/API_DESIGN.md` for the frontend-agnostic contract.

## Layout

```text
funnel/
├── backend/               # Python backend (only stack for now)
│   ├── src/funnel/
│   │   ├── models/        # dumb data only (Pydantic, no I/O, no logic)
│   │   ├── extraction/    # PDF text-extraction wrapper (pdfplumber → pypdf fallback)
│   │   ├── llm/           # auth + structured completion client (OpenRouter, OpenAI-compat)
│   │   ├── rubric/        # versioned scoring rubric + prompt builder (no I/O)
│   │   ├── repository/    # JSON-file store behind a Protocol (swap for DB later)
│   │   ├── services/      # orchestration + mutation (profiling, ranking, ingestion)
│   │   ├── api/           # HTTP only: FastAPI routers + DTO mapping, no business logic
│   │   ├── config.py      # env-only config, no instantiation
│   │   └── main.py        # composition root: wires everything (DI)
│   └── tests/             # mandatory per-layer tests
├── data/resumes/          # drop test PDFs here (git-ignored except .gitkeep)
├── docs/
│   ├── TECH_STACK.md
│   ├── ARCHITECTURE.md
│   ├── RUBRIC.md
│   └── API_DESIGN.md
├── frontend/              # placeholder until stack is decided
└── Plan.md                # original problem statement
```

## Quickstart (backend skeleton)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set OPENROUTER_API_KEY
pytest -q              # per-layer tests
uvicorn funnel.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the auto-generated OpenAPI UI.

## Design docs (read these first)

1. `docs/TECH_STACK.md` — why FastAPI / Pydantic v2 / pdfplumber+pypdf / OpenRouter.
2. `docs/ARCHITECTURE.md` — module boundaries, dependency rules, data flow.
3. `docs/RUBRIC.md` — scoring algorithm: LLM proposes evidence-bound scores,
   deterministic code aggregates and ranks (auditable).
4. `docs/API_DESIGN.md` — minimal REST surface the future frontend can rely on.

## Security note (internal HR PII)

Resumes are PII. Never commit PDFs or `data/store.json`. The LLM client sends
resume text to a third party (OpenRouter → upstream model provider) — review
your org's DPA / data-residency requirements before pointing at real data.
Production recommendation is Azure OpenAI with the same OpenAI-compatible
client (one-line `base_url` swap); see `docs/TECH_STACK.md`.
