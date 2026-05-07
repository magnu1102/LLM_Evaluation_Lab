import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { isTerminal, RunStateBadge } from "../components/RunStateBadge";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import type { Result, Status, TestCase } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const runId = Number(id);

  const [runQ, casesQ] = useQueries({
    queries: [
      {
        queryKey: ["run", runId],
        queryFn: () => api.getRun(runId),
        enabled: !Number.isNaN(runId),
        refetchInterval: (q: { state: { data?: { state?: string } } }) =>
          q.state.data && isTerminal(q.state.data.state as never) ? false : 1500,
      },
      { queryKey: ["test-cases"], queryFn: api.listTestCases },
    ],
  });

  if (Number.isNaN(runId)) return <p>Invalid run id.</p>;
  if (runQ.isLoading) return <p>Loading…</p>;
  if (runQ.error) return <pre style={{ color: "crimson" }}>{String(runQ.error)}</pre>;
  if (!runQ.data) return null;

  const run = runQ.data;
  const casesById = new Map<number, TestCase>(
    (casesQ.data ?? []).map((c) => [c.id, c]),
  );

  return (
    <section>
      <Link to="/">← Back to dashboard</Link>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginTop: 8,
        }}
      >
        <h2 style={{ margin: 0, display: "flex", gap: 12, alignItems: "center" }}>
          Run #{run.id} <RunStateBadge state={run.state} />
        </h2>
        <div style={{ display: "flex", gap: 8 }}>
          <a
            href={`${API_BASE}/runs/${run.id}/export.json`}
            style={{ fontSize: 14 }}
          >
            ⬇ JSON
          </a>
          <a
            href={`${API_BASE}/runs/${run.id}/export.csv`}
            style={{ fontSize: 14 }}
          >
            ⬇ CSV
          </a>
        </div>
      </div>
      <p style={{ color: "#666" }}>
        {run.provider} / {run.model} · started {new Date(run.started_at).toLocaleString()}
      </p>
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <span>Total: {run.summary.total}</span>
        <span>Passed: {run.summary.passed}</span>
        <span>Failed: {run.summary.failed}</span>
        <span>Needs review: {run.summary.needs_review}</span>
      </div>

      {run.state === "failed" && run.summary.error && (
        <div
          style={{
            background: "#f8d7da",
            color: "#721c24",
            padding: 12,
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          <strong>Run failed:</strong> {run.summary.error}
        </div>
      )}

      {(run.state === "pending" || run.state === "running") && (
        <p style={{ color: "#666", fontStyle: "italic" }}>
          Waiting for results — this view refreshes automatically.
        </p>
      )}

      <div style={{ display: "grid", gap: 16 }}>
        {run.results.map((r) => (
          <ResultCard key={r.id} result={r} testCase={casesById.get(r.test_case_id)} />
        ))}
      </div>
    </section>
  );
}

function ResultCard({ result, testCase }: { result: Result; testCase?: TestCase }) {
  const qc = useQueryClient();
  const [rating, setRating] = useState<Status | "">(result.human_rating ?? "");
  const [notes, setNotes] = useState(result.human_notes);

  const review = useMutation({
    mutationFn: () =>
      api.reviewResult(result.id, {
        human_rating: rating === "" ? null : rating,
        human_notes: notes,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["run", result.run_id] });
      qc.invalidateQueries({ queryKey: ["runs"] });
    },
  });

  return (
    <article
      style={{
        border: "1px solid #e5e5e5",
        borderRadius: 8,
        padding: 16,
        background: "#fff",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
        }}
      >
        <h3 style={{ margin: 0 }}>{testCase?.title ?? `Test case #${result.test_case_id}`}</h3>
        <StatusPill status={result.status} />
      </header>

      {testCase && (
        <details style={{ marginBottom: 12 }}>
          <summary style={{ cursor: "pointer", color: "#555" }}>question & context</summary>
          <p>
            <strong>Q:</strong> {testCase.question}
          </p>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              background: "#fafafa",
              padding: 8,
              borderRadius: 4,
              fontSize: 13,
            }}
          >
            {testCase.context}
          </pre>
        </details>
      )}

      <h4 style={{ margin: "8px 0 4px" }}>Model output</h4>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          background: "#fafafa",
          padding: 8,
          borderRadius: 4,
          fontSize: 13,
        }}
      >
        {result.model_output || <em>(empty)</em>}
      </pre>

      <h4 style={{ margin: "12px 0 4px" }}>Automatic checks</h4>
      <ul style={{ paddingLeft: 18, margin: 0 }}>
        {result.automatic_checks.map((c, i) => {
          const isJudge = c.criterion === "llm_judge";
          const color = isJudge
            ? "#3b3b8a"
            : c.passed
              ? "#155724"
              : "#721c24";
          const icon = isJudge ? "⚖" : c.passed ? "✓" : "✗";
          return (
            <li key={i} style={{ color }}>
              {icon} <strong>{c.criterion}</strong> ({c.severity})
              {c.detail ? ` — ${c.detail}` : ""}
            </li>
          );
        })}
        {result.automatic_checks.length === 0 && <li>(no checks ran)</li>}
      </ul>

      <h4 style={{ margin: "12px 0 4px" }}>Human review</h4>
      <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 8 }}>
        {(["pass", "needs_review", "fail"] as const).map((opt) => (
          <label key={opt}>
            <input
              type="radio"
              name={`rating-${result.id}`}
              checked={rating === opt}
              onChange={() => setRating(opt)}
            />{" "}
            {opt}
          </label>
        ))}
        <button type="button" onClick={() => setRating("")}>
          clear
        </button>
      </div>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notes…"
        rows={2}
        style={{ width: "100%", fontFamily: "inherit", fontSize: 14 }}
      />
      <div style={{ marginTop: 8, display: "flex", gap: 12, alignItems: "center" }}>
        <button
          type="button"
          onClick={() => review.mutate()}
          disabled={review.isPending}
          style={{
            padding: "6px 12px",
            background: "#3b5bdb",
            color: "white",
            border: 0,
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          {review.isPending ? "Saving…" : "Save review"}
        </button>
        {review.isSuccess && <span style={{ color: "#155724" }}>saved</span>}
        {review.error && <span style={{ color: "crimson" }}>{String(review.error)}</span>}
      </div>
    </article>
  );
}
