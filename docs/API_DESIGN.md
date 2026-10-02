# API design (minimal, frontend-agnostic)

Base prefix: `/api/v1`. JSON everywhere. Backend never returns HTML.
Frontend stack undecided — this contract is the only coupling.

## Endpoints

| Method & path | Request | Response | Notes |
|---|---|---|---|
| `GET /health` | — | `{status, version, rubric_version}` | liveness |
| `GET /api/v1/candidates?q=&tag=&limit=&offset=` | query | `{items: CandidateProfile[], total}` | search stub: `q` substring over name/skills; `tag` exact skill |
| `GET /api/v1/candidates/{id}` | — | `CandidateProfile` | 404 shape `{detail}` |
| `POST /api/v1/ingest` `{resume_dir?}` | optional override | `202 {scanned, ingested, needs_ocr, failed, errors[]}` | synchronous scan for v1 (async job later); idempotent; `needs_ocr` counts stored-but-flagged scans separately |
| `POST /api/v1/rank` | `{jd_text, rubric_version?, limit?}` | `{items: RankResult[], rubric_version}` | each scored independently, sorted by code |

## Shapes (see `backend/src/funnel/models/`)

- `CandidateProfile`: `id, name, email?, skills[], experience[], education[], summary?, source_file, file_hash, profile_status`.
- `RankResult`: `candidate_id, total_100, breakdown[{criterion, score_0_10, weight, evidence, confidence}], rationale, rubric_version`.
- Errors: FastAPI HTTPException `{detail}`; validation 422 with Pydantic body.

## Frontend thinking (just enough)

- Screens mappable 1:1: candidate table (`GET /candidates`), detail drawer
  (`GET /candidates/{id}`), JD input + ranked list (`POST /rank`), "Rescan folder"
  button (`POST /ingest`).
- No auth in skeleton (internal network assumed); add OIDC/proxy-auth before any
  non-local deploy — noted, not implemented.
- Pagination is offset/limit now; switch to cursor when profiles > ~5k.
- OpenAPI at `/docs` is the frontend contract source; DTOs in `api/` are the
  only place allowed to reshape service models for display.
