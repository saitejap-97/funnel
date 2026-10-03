# Funnel frontend (Vite + React + TS)

Internal SPA against the FastAPI backend. Three screens mapping 1:1 to
`docs/API_DESIGN.md`: candidate table (`/`), detail drawer
(`/candidates/:id`), JD rank form (`/rank`), plus a "Rescan folder" button
(`POST /ingest`).

## Run

```bash
npm install
npm run dev      # http://localhost:5173, /api proxied to :8000
```

Backend in another terminal (from `backend/`):

```bash
source .venv/bin/activate
set -a; source .env; set +a
PYTHONPATH=src uvicorn funnel.main:app --reload --port 8000
```

Production: `npm run build` → serve `dist/` anywhere; set
`VITE_API_BASE_URL` (see `.env.example`) to the backend origin. The backend
allows the dev origins via `CORS_ORIGINS`; extend it for the prod host.

## Layout

```text
src/
├── api/client.ts      # typed fetch client (mirrors backend models/)
├── pages/             # CandidatesPage, CandidateDetailPage, RankPage
├── App.tsx            # nav + routes
├── main.tsx           # entry
└── styles.css         # minimal styling, no framework
```

No auth yet (internal network assumed) — same caveat as the backend docs.
