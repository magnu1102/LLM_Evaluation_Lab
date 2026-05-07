import { useEffect, useState } from "react";

type Health = {
  status: string;
  db: boolean;
  provider: string;
  provider_configured: boolean;
};

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem", maxWidth: 720 }}>
      <h1>LLM Evaluation Lab</h1>
      <p>Phase 1 — skeleton. Backend health below.</p>
      {error && <pre style={{ color: "crimson" }}>Error: {error}</pre>}
      {health && (
        <ul>
          <li>status: {health.status}</li>
          <li>db: {String(health.db)}</li>
          <li>provider: {health.provider}</li>
          <li>provider configured: {String(health.provider_configured)}</li>
        </ul>
      )}
      {!health && !error && <p>Loading…</p>}
    </main>
  );
}
