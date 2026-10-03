import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type CandidateProfile, type RankResult } from "../api/client";
import { ResumeCard } from "../components/ResumeCard";

interface Row extends RankResult {
  profile: CandidateProfile;
}

export default function JobMatchesPage() {
  const { id } = useParams();
  const [title, setTitle] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [rubric, setRubric] = useState("");
  const [status, setStatus] = useState("Scoring… (one LLM call per candidate)");

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const job = await api.job(id);
        setTitle(job.title);
        const body = await api.rank({ jd_id: id });
        setRubric(body.rubric_version);
        const all = await api.candidates({ limit: 200 });
        const byId = new Map(all.items.map((c) => [c.id, c]));
        setRows(
          body.items.flatMap((r) => {
            const profile = byId.get(r.candidate_id);
            return profile ? [{ ...r, profile }] : [];
          }),
        );
        setStatus("");
      } catch (e) {
        setStatus(`Error: ${(e as Error).message}`);
      }
    })();
  }, [id]);

  return (
    <section>
      <p>
        <Link to="/">← Job descriptions</Link>
      </p>
      <h2>
        {title || "…"} {rubric && <span className="muted">(rubric {rubric})</span>}
      </h2>
      {status && <p className="muted">{status}</p>}
      <div className="grid">
        {rows.map((r) => (
          <ResumeCard key={r.candidate_id} profile={r.profile} result={r} />
        ))}
      </div>
    </section>
  );
}
