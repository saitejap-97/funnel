import { useEffect, useRef, useState } from "react";
import { api, type CandidateProfile } from "../api/client";
import { ResumeCard } from "../components/ResumeCard";

const DEBOUNCE_MS = 250;

type Best = Record<string, { score: number; job_title: string }>;

export default function CandidatesPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<CandidateProfile[]>([]);
  const [best, setBest] = useState<Best>({});
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("Type to search — results update as you type.");
  const [searching, setSearching] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced live search over the FULL resume text; results arrive
  // sorted by pre-computed best rating (desc).
  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    setSearching(true);
    timer.current = setTimeout(async () => {
      try {
        const body = await api.candidates({ q });
        setItems(body.items);
        setBest(body.best ?? {});
        setTotal(body.total);
        setStatus(body.total === 0 ? "No candidates match." : "");
      } catch (e) {
        setStatus(`Error: ${(e as Error).message}`);
      } finally {
        setSearching(false);
      }
    }, DEBOUNCE_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [q]);

  return (
    <section>
      <h2>Search candidates {total > 0 && <span className="muted">({total})</span>}</h2>
      <div className="row">
        <input
          className="search"
          placeholder="Search skills, roles, companies… e.g. C++"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoFocus
        />
        {searching && <span className="muted small">…</span>}
      </div>
      {status && <p className="muted">{status}</p>}
      <div className="grid">
        {items.map((c) => (
          <ResumeCard key={c.id} profile={c} best={best[c.id]} />
        ))}
      </div>
    </section>
  );
}
