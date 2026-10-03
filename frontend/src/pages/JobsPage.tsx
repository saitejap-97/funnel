import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type JobDescription } from "../api/client";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [status, setStatus] = useState("Loading job descriptions…");
  const [jd, setJd] = useState("");

  useEffect(() => {
    api
      .jobs()
      .then((b) => {
        setJobs(b.items);
        setStatus(b.items.length === 0 ? "No job descriptions yet — run Rescan." : "");
      })
      .catch((e) => setStatus(`Error: ${(e as Error).message}`));
  }, []);

  async function rescan() {
    setStatus("Scanning folders…");
    try {
      const s = await api.ingest();
      setStatus(
        `Resumes: ${s.ingested}/${s.scanned} ok · JDs: ${s.jobs_ingested}/${s.jobs_scanned} ok` +
          (s.errors.length ? ` · Errors: ${s.errors.join("; ")}` : ""),
      );
      setJobs((await api.jobs()).items);
    } catch (e) {
      setStatus(`Error: ${(e as Error).message}`);
    }
  }

  return (
    <section>
      <h2>Job descriptions</h2>
      <div className="row">
        <button onClick={rescan}>Rescan folders</button>
      </div>
      {status && <p className="muted">{status}</p>}
      <div className="grid">
        {jobs.map((j) => (
          <Link key={j.id} to={`/jobs/${j.id}`} className="jd-card">
            <strong>{j.title || "(untitled)"}</strong>
            <span className="muted small">Click to see sorted matches →</span>
          </Link>
        ))}
      </div>
      <h3>…or paste a custom JD</h3>
      <textarea
        rows={4}
        placeholder="Paste a job description to rank against it directly"
        value={jd}
        onChange={(e) => setJd(e.target.value)}
      />
      <div className="row">
        <Link
          to={`/rank-custom?jd=${encodeURIComponent(jd)}`}
          className={jd.trim() ? "btn" : "btn disabled"}
          aria-disabled={!jd.trim()}
        >
          Rank against this JD
        </Link>
      </div>
    </section>
  );
}
