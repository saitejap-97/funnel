# Architecture — module boundaries & data flow

## The six modules (as requested) + two seams

```text
resumes/*.pdf
  │ 1. extraction/  — wraps pdf library. Input: Path. Output: ResumeRaw.
  │                  Knows NOTHING about LLMs or HR.
  ▼
ResumeRaw (models)
  │ 2. llm/ + rubric/ — llm/ is dumb transport (auth + structured completion).
  │                      rubric/ owns versioned criteria + prompt builder + JSON schema.
  │                      No prompts outside rubric/. No business logic inside llm/.
  ▼
CandidateProfile (models, dumb Pydantic)
  │ 3. repository/ — persists profiles (JSON file now, Protocol for DB later).
  │                  Owns atomic writes/locks. Services never touch JSON directly.
  ▼
store.json
```

Serving path:

```text
HTTP → 5. api/ (FastAPI routers: parse/validate/map only)
      → 4. services/ (profiling, ranking, ingestion: orchestration + mutation)
      → repository/ + llm/ + extraction/
      → DTO → HTTP
6. main.py composes everything (only place that instantiates clients/stores).
```

## Dependency rules (enforced by review, not just convention)

1. `models/` imports nothing from other `funnel.*` modules. No methods with I/O.
2. `llm/` imports `models/` (for schemas) and stdlib only. No rubric text, no ranking math.
3. `rubric/` imports `models/` only. Pure functions: `build_prompt()`, `aggregate()`.
4. `repository/` imports `models/` only. No LLM, no HTTP.
5. `services/` imports all of the above; owns orchestration. Never touches disk/HTTP directly except via injected Protocols.
6. `api/` imports `services/` + `models/`. No LLM/extraction/repository imports. Maps service results → response DTOs.
7. `config.py` reads env only. `main.py` is the sole composition root.

Two extra seams (from design review):
- `rubric/` is separate from `services/ranking.py` so scoring criteria are
  versioned/auditable and prompts can't drift across the codebase.
- File-watching is future `services/ingestion.scan()` (pure orchestration over
  an injected directory listing) — no `watchdog` inside services; the watcher
  adapter can be added under `services/` or `api/` trigger without breaking tests.

## Data flow: ingest → rank

1. **Ingest** (`POST /ingest` or startup scan): list `RESUME_DIR/*.pdf` →
   `extraction.extract(path)` → `ResumeRaw` → `services/profiling.build_profile(raw)`
   (calls `llm.complete_json(prompt, schema)`) → validate `CandidateProfile` →
   `repository.upsert()`. Idempotent on `(file_hash)`: re-ingest updates.
2. **Rank** (`POST /rank {jd_text, rubric_version, limit}`): load profiles →
   `rubric.build_rank_prompt(profile, jd)` → `llm.complete_json` per candidate
   (async fan-out, bounded concurrency) → `rubric.aggregate()` deterministic
   weighted sum → sort desc → return `RankResult[]` with per-criterion evidence.
   LLM proposes, code disposes: ties/weights are pure math, reproducible.

## Failure handling

- Empty/short extraction → `needs_ocr` flag, never sent to LLM as "no experience".
- LLM invalid JSON → 1 repair retry ("fix to schema, no prose"), else mark
  `profile_status=failed` with error, don't store partial.
- Prompt injection (resumes are untrusted data): system prompt isolates resume
  as DATA in XML tags, temperature 0, no tool side-effects, human review gate
  before any auto-decision.
