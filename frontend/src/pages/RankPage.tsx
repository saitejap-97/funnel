import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type CandidateProfile, type RankResult } from "../api/client";

interface Row extends RankResult {
  name: string;
}

export default function RankPage() {
  const [jd, setJd] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [rubric, setRubric] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function runRank() {
    if (!jd.trim()) {
      setStatus("Paste a job description first.");
      return;
    }
    setBusy(true);
    setStatus("Scoring… (one LLM call per candidate)");
    try {
      const body = await api.rank(jd, 20);
      setRubric(body.rubric_version);
      // Names need a lookup: fetch the (small) candidate list once.
      const all = await api.candidates({ limit: 200 });
      const names = new Map<string, CandidateProfile>(
        all.items.map((c) => [c.id, c]),
      );
      setRows(
        body.items.map((r) => ({
          ...r,
          name: names.get(r.candidate_id)?.name ?? r.candidate_id,
        })),
      );
      setStatus("");
    } catch (e) {
      setStatus(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Rank by job description {rubric && <span className="muted">(rubric {rubric})</span>}</h2>
      <textarea
        rows={6}
        placeholder="Paste the JD here: title, required stack, scope…"
        value={jd}
        onChange={(e) => setJd(e.target.value)}
      />
      <div className="row">
        <button onClick={runRank} disabled={busy}>
          {busy ? "Scoring…" : "Rank candidates"}
        </button>
      </div>
      {status && <p className="muted">{status}</p>}
      {rows.map((r) => (
        <div key={r.candidate_id} className="card">
          <strong>
            {r.total_100.toFixed(1)}
          </strong>{" "}
          <Link to={`/candidates/${r.candidate_id}`}>{r.name}</Link>
          <p className="muted">{r.rationale}</p>
          {r.breakdown.map((b) => (
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
        </div>
      ))}
    </section>
  );
}
