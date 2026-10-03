import { Link, Route, Routes } from "react-router-dom";
import CandidatesPage from "./pages/CandidatesPage";
import CandidateDetailPage from "./pages/CandidateDetailPage";
import RankPage from "./pages/RankPage";

export default function App() {
  return (
    <>
      <header>
        <h1>Funnel</h1>
        <nav>
          <Link to="/">Candidates</Link>
          <Link to="/rank">Rank by JD</Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<CandidatesPage />} />
          <Route path="/candidates/:id" element={<CandidateDetailPage />} />
          <Route path="/rank" element={<RankPage />} />
        </Routes>
      </main>
    </>
  );
}
