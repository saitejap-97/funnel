# Rubric & ranking algorithm (v1, versioned)

`rubric_version` is stored on every `RankResult` so HR can audit/reproduce.
Current version: **`v1`**.

## Criteria (weights sum to 1.0)

| key | label | weight | 0–10 meaning |
|---|---|---|---|
| `skills_match` | Skills match to JD | 0.35 | 0 = none of the required stack; 10 = all + depth evidence |
| `experience_relevance` | Relevant experience | 0.30 | years + domain closeness |
| `education_fit` | Education fit | 0.10 | degree/field relevance (never a hard filter) |
| `impact_signals` | Impact / scope signals | 0.15 | quantified outcomes, scope, ownership |
| `growth_trajectory` | Trajectory | 0.10 | progression, learning velocity |

## Algorithm

1. For each candidate, the LLM returns per-criterion `{score_0_10, evidence, confidence_0_1}`
   constrained to the JSON schema in `rubric/default_rubric.py`. Evidence must be
   a short quote/paraphrase traceable to the profile (page ref when available).
2. Code validates `0 <= score <= 10`, then computes:

   ```text
   total_100 = round(sum(score_c * weight_c for c in criteria) * 10, 1)
   ```

   Deterministic, no LLM math. Ties broken by `skills_match`, then `experience_relevance`,
   then `candidate_id` (stable).
3. `POST /rank` sorts by `total_100` desc and returns `breakdown[]` + `rationale`
   (1–2 sentences assembled from top evidence, or LLM's capped 280-char string).

## Calibration & guardrails

- `temperature=0`, JD + profile only (no cross-candidate comparison in one call —
  avoids position bias; each scored independently, ranked by code).
- Missing info scores low with `confidence` low and `evidence=""` — never infer.
- Education is low-weight by design; employment gaps / non-traditional paths must
  not be penalized in `growth_trajectory` without evidence.
- When HR disagrees, bump `rubric_version` (copy `default_rubric.py` → `v2`) —
  old results stay comparable.

## Future ideas (not v1)

- Pairwise LLM re-rank of top-k only (cost control).
- Skill-tag normalization table (e.g., "k8s" → "kubernetes") before scoring.
- Blind mode (strip name/email/photo refs) for fairness audits.
