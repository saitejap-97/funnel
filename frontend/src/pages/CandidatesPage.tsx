import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type CandidateProfile } from "../api/client";

export default function CandidatesPage() {
  const [q, setQ] = useState("");
  const [tag, setTag] = useState("");
  const [items, setItems] = useState<CandidateProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("Search or rescan to load candidates.");
  const [busy, setBusy] = useState(false);

  async function search() {
    setBusy(true);
    try {
      const body = await api.candidates({ q, tag });
      setItems(body.items);
      setTotal(body.total);
      setStatus(body.total === 0 ? "No candidates match." : "");
    } catch (e) {
      setStatus(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function rescan() {
    setBusy(true);
    try {
      const s = await api.ingest();
      setStatus(
        `Scanned ${s.scanned}: ingested ${s.ingested}, needs_ocr ${s.needs_ocr}, failed ${s.failed}.` +
          (s.errors.length ? ` Errors: ${s.errors.join("; ")}` : " Now search to refresh."),
      );
    } catch (e) {
      setStatus(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Candidates {total > 0 && <span className="muted">({total})</span>}</h2>
      <div className="row">
        <input
          placeholder="Search name, skills…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <input
          placeholder="Skill tag (exact)"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <button onClick={search} disabled={busy}>Search</button>
        <button onClick={rescan} disabled={busy} title="Re-scan the resume folder">
          Rescan folder
        </button>
      </div>
      {status && <p className="muted">{status}</p>}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Skills</th>
            <th>Experience</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.id}>
              <td>
                <Link to={`/candidates/${c.id}`}>{c.name || "(unnamed)"}</Link>
              </td>
              <td>{c.skills.slice(0, 5).join(", ")}</td>
              <td>{c.experience.length} role(s)</td>
              <td>
                <span className={`pill ${c.profile_status}`}>{c.profile_status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
