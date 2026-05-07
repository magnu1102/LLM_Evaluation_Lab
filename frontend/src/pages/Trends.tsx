import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link } from "react-router-dom";

import { api } from "../lib/api";
import type { PromptTemplate, Run } from "../types";

interface PromptSeries {
  promptId: number;
  name: string;
  version: number;
  runs: Run[];
  latestPassRate: number | null;
}

const COLORS = {
  pass: "#28a745",
  fail: "#dc3545",
  needs_review: "#ffc107",
  empty: "#e5e5e5",
} as const;

const cardStyle = {
  border: "1px solid #e5e5e5",
  borderRadius: 8,
  padding: 16,
  background: "#fff",
} as const;

function passRate(run: Run): number | null {
  return run.summary.total > 0 ? run.summary.passed / run.summary.total : null;
}

function overallStatus(run: Run): "pass" | "fail" | "needs_review" {
  if (run.summary.failed > 0) return "fail";
  if (run.summary.needs_review > 0) return "needs_review";
  return "pass";
}

export function TrendsPage() {
  const [runsQ, promptsQ] = useQueries({
    queries: [
      { queryKey: ["runs"], queryFn: api.listRuns },
      { queryKey: ["prompt-templates"], queryFn: api.listPromptTemplates },
    ],
  });

  const series: PromptSeries[] = useMemo(() => {
    if (!runsQ.data || !promptsQ.data) return [];
    const promptsById = new Map<number, PromptTemplate>(
      promptsQ.data.map((p) => [p.id, p]),
    );
    const buckets = new Map<number, Run[]>();
    for (const r of runsQ.data) {
      if (!promptsById.has(r.prompt_template_id)) continue;
      const list = buckets.get(r.prompt_template_id) ?? [];
      list.push(r);
      buckets.set(r.prompt_template_id, list);
    }
    const out: PromptSeries[] = [];
    for (const [promptId, runs] of buckets) {
      const sorted = [...runs].sort(
        (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime(),
      );
      const latest = sorted[sorted.length - 1];
      const p = promptsById.get(promptId)!;
      out.push({
        promptId,
        name: p.name,
        version: p.version,
        runs: sorted,
        latestPassRate: latest ? passRate(latest) : null,
      });
    }
    return out.sort(
      (a, b) =>
        a.name.localeCompare(b.name) || a.version - b.version,
    );
  }, [runsQ.data, promptsQ.data]);

  return (
    <section>
      <h2>Trends</h2>
      <p style={{ color: "#555" }}>
        Pass rate per prompt name@version over time. Each cell is one run, oldest
        on the left. Click a run to open it.
      </p>

      {(runsQ.isLoading || promptsQ.isLoading) && <p>Loading…</p>}
      {(runsQ.error || promptsQ.error) && (
        <pre style={{ color: "crimson" }}>
          {String(runsQ.error ?? promptsQ.error)}
        </pre>
      )}

      {series.length === 0 && runsQ.data && promptsQ.data && (
        <p>No runs yet. Create one from the New run page.</p>
      )}

      <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
        {series.map((s) => (
          <PromptTrendCard key={s.promptId} series={s} />
        ))}
      </div>
    </section>
  );
}

function PromptTrendCard({ series }: { series: PromptSeries }) {
  return (
    <article style={cardStyle}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 12,
        }}
      >
        <h3 style={{ margin: 0 }}>
          {series.name}@{series.version}
        </h3>
        <span style={{ color: "#666", fontSize: 13 }}>
          {series.runs.length} run{series.runs.length === 1 ? "" : "s"}
          {series.latestPassRate !== null && (
            <> · latest pass rate {(series.latestPassRate * 100).toFixed(0)}%</>
          )}
        </span>
      </header>

      <RunSparkline runs={series.runs} />
      <Sparkline runs={series.runs} />
    </article>
  );
}

function RunSparkline({ runs }: { runs: Run[] }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        flexWrap: "wrap",
        marginBottom: 12,
      }}
    >
      {runs.map((r) => {
        const status = overallStatus(r);
        const color = COLORS[status];
        return (
          <Link
            key={r.id}
            to={`/runs/${r.id}`}
            title={`Run #${r.id} · ${new Date(r.started_at).toLocaleString()} · ${r.summary.passed}/${r.summary.total} passed`}
            style={{
              width: 18,
              height: 18,
              borderRadius: 3,
              background: color,
              display: "inline-block",
              border: "1px solid rgba(0,0,0,0.1)",
            }}
          />
        );
      })}
    </div>
  );
}

function Sparkline({ runs }: { runs: Run[] }) {
  const W = 480;
  const H = 80;
  const PAD = 4;

  if (runs.length === 0) return null;

  const points = runs
    .map((r, i) => {
      const rate = passRate(r);
      if (rate === null) return null;
      const x = runs.length === 1 ? W / 2 : PAD + (i * (W - 2 * PAD)) / (runs.length - 1);
      const y = PAD + (1 - rate) * (H - 2 * PAD);
      return { x, y, rate, run: r };
    })
    .filter((p): p is NonNullable<typeof p> => p !== null);

  if (points.length === 0) return null;

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      style={{ display: "block", maxWidth: 480, background: "#fafafa", borderRadius: 4 }}
    >
      <line x1={PAD} y1={PAD} x2={W - PAD} y2={PAD} stroke="#eee" />
      <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="#eee" />
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="#eee" />
      {points.length > 1 && (
        <path d={path} fill="none" stroke="#3b5bdb" strokeWidth={2} />
      )}
      {points.map((p) => (
        <circle key={p.run.id} cx={p.x} cy={p.y} r={3} fill="#3b5bdb">
          <title>
            {`Run #${p.run.id} · ${(p.rate * 100).toFixed(0)}% pass · ${new Date(p.run.started_at).toLocaleString()}`}
          </title>
        </circle>
      ))}
    </svg>
  );
}
