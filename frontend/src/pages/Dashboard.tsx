import { useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import type { PromptTemplate, Run } from "../types";

const td = { padding: "8px 12px", borderBottom: "1px solid #eee" } as const;

export function DashboardPage() {
  const [runsQ, promptsQ] = useQueries({
    queries: [
      { queryKey: ["runs"], queryFn: api.listRuns },
      { queryKey: ["prompt-templates"], queryFn: api.listPromptTemplates },
    ],
  });

  const promptsById = new Map<number, PromptTemplate>(
    (promptsQ.data ?? []).map((p) => [p.id, p]),
  );

  const overallStatus = (run: Run) => {
    if (run.summary.failed > 0) return "fail" as const;
    if (run.summary.needs_review > 0) return "needs_review" as const;
    return "pass" as const;
  };

  return (
    <section>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h2>Recent runs</h2>
        <Link to="/runs/new">New run →</Link>
      </div>

      {runsQ.isLoading && <p>Loading…</p>}
      {runsQ.error && <pre style={{ color: "crimson" }}>{String(runsQ.error)}</pre>}
      {runsQ.data && runsQ.data.length === 0 && (
        <p>No runs yet. Create one from the New run page.</p>
      )}

      {runsQ.data && runsQ.data.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 12 }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#fafafa" }}>
              <th style={td}>Run</th>
              <th style={td}>Prompt</th>
              <th style={td}>Provider / model</th>
              <th style={td}>Started</th>
              <th style={td}>Pass</th>
              <th style={td}>Fail</th>
              <th style={td}>Review</th>
              <th style={td}>Status</th>
            </tr>
          </thead>
          <tbody>
            {runsQ.data.map((run) => {
              const p = promptsById.get(run.prompt_template_id);
              const label = p ? `${p.name}@${p.version}` : `#${run.prompt_template_id}`;
              return (
                <tr key={run.id}>
                  <td style={td}>
                    <Link to={`/runs/${run.id}`}>#{run.id}</Link>
                  </td>
                  <td style={td}>{label}</td>
                  <td style={td}>
                    {run.provider} / {run.model}
                  </td>
                  <td style={td}>{new Date(run.started_at).toLocaleString()}</td>
                  <td style={td}>{run.summary.passed}</td>
                  <td style={td}>{run.summary.failed}</td>
                  <td style={td}>{run.summary.needs_review}</td>
                  <td style={td}>
                    <StatusPill status={overallStatus(run)} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
