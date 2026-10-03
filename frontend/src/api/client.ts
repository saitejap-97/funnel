// Typed client for the FastAPI backend. Mirrors backend/src/funnel/models/.
// Contract source: GET /docs (OpenAPI) + docs/API_DESIGN.md.

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export interface Experience {
  title: string;
  company: string;
  years: number;
  summary: string;
}

export interface Education {
  degree: string;
  school: string;
  year: number | null;
}

export interface CandidateProfile {
  id: string;
  name: string;
  email: string | null;
  skills: string[];
  experience: Experience[];
  education: Education[];
  summary: string;
  tags: string[];
  source_file: string;
  file_hash: string;
  profile_status: "ok" | "needs_ocr" | "failed";
}

export interface CriterionScore {
  criterion: string;
  score_0_10: number;
  weight: number;
  evidence: string;
  confidence: number;
}

export interface RankResult {
  candidate_id: string;
  total_100: number;
  breakdown: CriterionScore[];
  rationale: string;
  rubric_version: string;
}

export interface JobDescription {
  id: string;
  title: string;
  source_file: string;
  file_hash: string;
  full_text: string;
}

export interface IngestSummary {
  scanned: number;
  ingested: number;
  needs_ocr: number;
  failed: number;
  jobs_scanned: number;
  jobs_ingested: number;
  jobs_failed: number;
  errors: string[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status} ${path}: ${body.slice(0, 200)}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  health: () =>
    request<{ status: string; version: string; rubric_version: string }>(
      "/health",
    ),
  candidates: (params: { q?: string; tag?: string; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.tag) qs.set("tag", params.tag);
    qs.set("limit", String(params.limit ?? 50));
    qs.set("offset", String(params.offset ?? 0));
    return request<{ items: CandidateProfile[]; total: number }>(
      `/api/v1/candidates?${qs}`,
    );
  },
  candidate: (id: string) =>
    request<CandidateProfile>(`/api/v1/candidates/${id}`),
  ingest: (resume_dir?: string, jd_dir?: string) =>
    request<IngestSummary>(
      "/api/v1/ingest",
      { method: "POST", body: JSON.stringify({ resume_dir, jd_dir }) },
    ),
  jobs: () => request<{ items: JobDescription[] }>("/api/v1/jobs"),
  job: (id: string) => request<JobDescription>(`/api/v1/jobs/${id}`),
  rank: (args: { jd_text?: string; jd_id?: string; limit?: number }) =>
    request<{ items: RankResult[]; rubric_version: string }>("/api/v1/rank", {
      method: "POST",
      body: JSON.stringify({ jd_text: args.jd_text ?? "", jd_id: args.jd_id ?? null, limit: args.limit ?? 20 }),
    }),
};
