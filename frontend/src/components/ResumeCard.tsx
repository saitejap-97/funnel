import { Link } from "react-router-dom";
import type { CandidateProfile, RankResult } from "../api/client";

/** Deterministic hue from a string — stable avatar color per candidate. */
export function hueFor(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  return h;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Latest role as a one-line headline, e.g. "Senior SWE @ Northwind". */
export function headlineOf(c: CandidateProfile): string {
  const latest = c.experience[0];
  if (!latest) return c.skills.slice(0, 3).join(" · ") || "—";
  return `${latest.title}${latest.company ? ` @ ${latest.company}` : ""}`;
}

export function Avatar({ name, id }: { name: string; id: string }) {
  return (
    <span
      className="avatar"
      style={{ background: `hsl(${hueFor(id)}, 55%, 42%)` }}
      aria-hidden
    >
      {initials(name)}
    </span>
  );
}

function ScoreBadge({ value }: { value: number }) {
  const cls = value >= 75 ? "high" : value >= 50 ? "mid" : "low";
  return <span className={`score ${cls}`}>{value.toFixed(1)}</span>;
}

export function ResumeCard({
  profile,
  result,
}: {
  profile: CandidateProfile;
  result?: RankResult;
}) {
  return (
    <article className="resume-card">
      <div className="resume-top">
        <Avatar name={profile.name} id={profile.id} />
        <div className="resume-head">
          <Link to={`/candidates/${profile.id}`} className="resume-name">
            {profile.name || "(unnamed)"}
          </Link>
          <div className="muted small">{headlineOf(profile)}</div>
        </div>
        {result && <ScoreBadge value={result.total_100} />}
      </div>
      {profile.summary && <p className="resume-summary">{profile.summary}</p>}
      {profile.skills.length > 0 && (
        <div className="chips">
          {profile.skills.slice(0, 6).map((s) => (
            <span key={s} className="chip">
              {s}
            </span>
          ))}
        </div>
      )}
      {result && (
        <>
          <p className="muted small">{result.rationale}</p>
          <details>
            <summary className="small">Score breakdown</summary>
            {result.breakdown.map((b) => (
              <div key={b.criterion} className="bar-row">
                <span className="bar-label">{b.criterion}</span>
                <span className="bar">
                  <span
                    className="bar-fill"
                    style={{ width: `${b.score_0_10 * 10}%` }}
                  />
                </span>
                <span className="muted">{b.score_0_10.toFixed(1)}</span>
              </div>
            ))}
          </details>
        </>
      )}
    </article>
  );
}
