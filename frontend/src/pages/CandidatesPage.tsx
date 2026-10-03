import { useState } from "react";
import { api, type CandidateProfile } from "../api/client";
import { ResumeCard } from "../components/ResumeCard";

export default function CandidatesPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<CandidateProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("Type a skill like C++ and hit Search.");
  const [busy, setBusy] = useState(false);

  async function search() {
    setBusy(true);
    try {
      const body = await api.candidates({ q });
      setItems(body.items);
      setTotal(body.total);
      setStatus(body.total === 0 ? "No candidates match." : "");
    } catch (e) {
      setStatus(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Search candidates {total > 0 && <span className="muted">({total})</span>}</h2>
      <div className="row">
        <input
          className="search"
          placeholder="Search skills, roles, companies… e.g. C++"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <button onClick={search} disabled={busy}>
          Search
        </button>
      </div>
      {status && <p className="muted">{status}</p>}
      <div className="grid">
        {items.map((c) => (
          <ResumeCard key={c.id} profile={c} />
        ))}
      </div>
    </section>
  );
}
