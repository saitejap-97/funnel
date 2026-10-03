import { Link, Route, Routes } from "react-router-dom";
import JobsPage from "./pages/JobsPage";
import JobMatchesPage from "./pages/JobMatchesPage";
import CandidatesPage from "./pages/CandidatesPage";
import CandidateDetailPage from "./pages/CandidateDetailPage";
import RankPage from "./pages/RankPage";

export default function App() {
  return (
    <>
      <header>
        <h1>Funnel</h1>
        <nav>
          <Link to="/">Jobs</Link>
          <Link to="/candidates">Candidates</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobMatchesPage />} />
          <Route path="/candidates" element={<CandidatesPage />} />
          <Route path="/candidates/:id" element={<CandidateDetailPage />} />
          <Route path="/rank-custom" element={<RankPage />} />
        </Routes>
      </main>
    </>
  );
}
