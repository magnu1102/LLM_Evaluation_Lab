import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

export function HealthPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 5000,
  });

  return (
    <section>
      <h2>Health</h2>
      {isLoading && <p>Loading…</p>}
      {error && <pre style={{ color: "crimson" }}>{String(error)}</pre>}
      {data && (
        <ul>
          <li>status: {data.status}</li>
          <li>db: {String(data.db)}</li>
          <li>provider: {data.provider}</li>
        </ul>
      )}
    </section>
  );
}
