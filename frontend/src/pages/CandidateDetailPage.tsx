import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type CandidateProfile } from "../api/client";

export default function CandidateDetailPage() {
  const { id } = useParams();
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api
      .candidate(id)
      .then(setProfile)
      .catch((e) => setError((e as Error).message));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!profile) return <p className="muted">Loading…</p>;

  return (
    <section>
      <p>
        <Link to="/">← Candidates</Link>
      </p>
      <h2>{profile.name || "(unnamed)"}</h2>
      <p className="muted">
        {[profile.email, profile.source_file.split("/").pop()].filter(Boolean).join(" · ")}
      </p>
      {profile.summary && <p>{profile.summary}</p>}
      <h3>Skills</h3>
      <p>{profile.skills.join(", ") || "—"}</p>
      <h3>Experience</h3>
      {profile.experience.map((e, i) => (
        <div key={i} className="card">
          <strong>
            {e.title} @ {e.company}
          </strong>{" "}
          <span className="muted">({e.years}y)</span>
          <p>{e.summary}</p>
        </div>
      ))}
      <h3>Education</h3>
      {profile.education.map((e, i) => (
        <div key={i}>
          {e.degree} — {e.school}
          {e.year ? ` (${e.year})` : ""}
        </div>
      ))}
      {profile.tags.length > 0 && (
        <>
          <h3>Tags</h3>
          <p>{profile.tags.join(", ")}</p>
        </>
      )}
    </section>
  );
}
