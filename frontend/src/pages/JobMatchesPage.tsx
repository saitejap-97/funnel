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
  const [cached, setCached] = useState(false);
  const [status, setStatus] = useState("Loading…");

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const job = await api.job(id);
        setTitle(job.title);
        // Stale-while-revalidate: instant when cached, scores only
        // new/changed pairs otherwise.
        const body = await api.matches(id);
        setRubric(body.rubric_version);
        setCached(body.cached);
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
        {title || "…"} {rubric && <span className="muted">(rubric {rubric})</span>}{" "}
        {rows.length > 0 && (
          <span className="muted small">{cached ? "⚡ cached" : "freshly scored"}</span>
        )}
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
