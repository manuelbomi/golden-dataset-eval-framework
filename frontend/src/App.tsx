import { NavLink, Route, Routes } from "react-router-dom";
import { AdjudicationPage } from "./pages/AdjudicationPage";
import { GoldenPage } from "./pages/GoldenPage";
import { QueuePage } from "./pages/QueuePage";

export function App() {
  return (
    <div className="app-shell">
      <header>
        <h1>Golden Dataset &amp; Evaluation Framework</h1>
        <nav>
          <NavLink to="/" end>
            Annotate
          </NavLink>
          <NavLink to="/adjudication">Adjudication</NavLink>
          <NavLink to="/golden">Golden set</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<QueuePage />} />
        <Route path="/adjudication" element={<AdjudicationPage />} />
        <Route path="/golden" element={<GoldenPage />} />
      </Routes>
    </div>
  );
}
