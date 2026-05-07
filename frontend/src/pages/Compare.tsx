import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import type { PromptTemplate, Result, Run, Status, TestCase } from "../types";

type Bucket = "improved" | "regressed" | "changed" | "unchanged";

interface Row {
  testCaseId: number;
  title: string;
  a: Status | null;
  b: Status | null;
  bucket: Bucket;
}

function bucketFor(a: Status | null, b: Status | null): Bucket {
  if (a === b) return "unchanged";
  if (a !== "pass" && b === "pass") return "improved";
  if (a === "pass" && b !== "pass") return "regressed";
  return "changed";
}

function indexResults(run: Run | undefined): Map<number, Result> {
  const m = new Map<number, Result>();
  for (const r of run?.results ?? []) m.set(r.test_case_id, r);
  return m;
}

const sectionStyle = {
  border: "1px solid #e5e5e5",
  borderRadius: 8,
  padding: 12,
  background: "#fff",
};

export function ComparePage() {
  const [params, setParams] = useSearchParams();
  const aId = Number(params.get("a") ?? "");
  const bId = Number(params.get("b") ?? "");

  const [runsQ, casesQ, promptsQ, runAQ, runBQ] = useQueries({
    queries: [
      { queryKey: ["runs"], queryFn: api.listRuns },
      { queryKey: ["test-cases"], queryFn: api.listTestCases },
      { queryKey: ["prompt-templates"], queryFn: api.listPromptTemplates },
      {
        queryKey: ["run", aId],
        queryFn: () => api.getRun(aId),
        enabled: !!aId && !Number.isNaN(aId),
      },
      {
        queryKey: ["run", bId],
        queryFn: () => api.getRun(bId),
        enabled: !!bId && !Number.isNaN(bId),
      },
    ],
  });

  const casesById = useMemo(
    () => new Map<number, TestCase>((casesQ.data ?? []).map((c) => [c.id, c])),
    [casesQ.data],
  );
  const promptsById = useMemo(
    () => new Map<number, PromptTemplate>((promptsQ.data ?? []).map((p) => [p.id, p])),
    [promptsQ.data],
  );

  const rows: Row[] = useMemo(() => {
    if (!runAQ.data || !runBQ.data) return [];
    const a = indexResults(runAQ.data);
    const b = indexResults(runBQ.data);
    const ids = new Set<number>([...a.keys(), ...b.keys()]);
    const out: Row[] = [];
    for (const id of ids) {
      const aStatus = a.get(id)?.status ?? null;
      const bStatus = b.get(id)?.status ?? null;
      out.push({
        testCaseId: id,
        title: casesById.get(id)?.title ?? `Test case #${id}`,
        a: aStatus,
        b: bStatus,
        bucket: bucketFor(aStatus, bStatus),
      });
    }
    return out.sort((x, y) => x.title.localeCompare(y.title));
  }, [runAQ.data, runBQ.data, casesById]);

  const grouped = useMemo(() => {
    const g: Record<Bucket, Row[]> = {
      improved: [],
      regressed: [],
      changed: [],
      unchanged: [],
    };
    for (const r of rows) g[r.bucket].push(r);
    return g;
  }, [rows]);

  const setRun = (key: "a" | "b", value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  const labelForRun = (run: Run) => {
    const p = promptsById.get(run.prompt_template_id);
    const promptLabel = p ? `${p.name}@${p.version}` : `prompt #${run.prompt_template_id}`;
    return `#${run.id} · ${promptLabel} · ${run.provider}/${run.model}`;
  };

  return (
    <section>
      <h2>Compare runs</h2>
      <p style={{ color: "#555" }}>
        Pick two runs to see which test cases improved, regressed, or stayed the same.
      </p>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", margin: "12px 0 24px" }}>
        <RunSelector
          label="Baseline (A)"
          value={aId ? String(aId) : ""}
          runs={runsQ.data ?? []}
          onChange={(v) => setRun("a", v)}
          labelForRun={labelForRun}
        />
        <RunSelector
          label="Candidate (B)"
          value={bId ? String(bId) : ""}
          runs={runsQ.data ?? []}
          onChange={(v) => setRun("b", v)}
          labelForRun={labelForRun}
        />
      </div>

      {runsQ.isLoading && <p>Loading runs…</p>}
      {!aId || !bId ? (
        <p style={{ color: "#666" }}>Select two runs above.</p>
      ) : runAQ.isLoading || runBQ.isLoading ? (
        <p>Loading run data…</p>
      ) : runAQ.error || runBQ.error ? (
        <pre style={{ color: "crimson" }}>{String(runAQ.error ?? runBQ.error)}</pre>
      ) : (
        <div style={{ display: "grid", gap: 16 }}>
          <SummaryStrip grouped={grouped} />
          <Group title="Regressed" rows={grouped.regressed} accent="#f8d7da" />
          <Group title="Improved" rows={grouped.improved} accent="#d4edda" />
          <Group title="Changed (other)" rows={grouped.changed} accent="#fff3cd" />
          <Group title="Unchanged" rows={grouped.unchanged} accent="#f3f3f3" />
        </div>
      )}
    </section>
  );
}

function RunSelector({
  label,
  value,
  runs,
  onChange,
  labelForRun,
}: {
  label: string;
  value: string;
  runs: Run[];
  onChange: (v: string) => void;
  labelForRun: (run: Run) => string;
}) {
  return (
    <label style={{ display: "grid", gap: 4, minWidth: 320 }}>
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">— select run —</option>
        {runs.map((r) => (
          <option key={r.id} value={r.id}>
            {labelForRun(r)}
          </option>
        ))}
      </select>
    </label>
  );
}

function SummaryStrip({ grouped }: { grouped: Record<Bucket, Row[]> }) {
  const total =
    grouped.improved.length +
    grouped.regressed.length +
    grouped.changed.length +
    grouped.unchanged.length;
  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        padding: 12,
        background: "#fafafa",
        borderRadius: 8,
        border: "1px solid #eee",
      }}
    >
      <span>Total cases: {total}</span>
      <span style={{ color: "#155724" }}>Improved: {grouped.improved.length}</span>
      <span style={{ color: "#721c24" }}>Regressed: {grouped.regressed.length}</span>
      <span style={{ color: "#856404" }}>Other change: {grouped.changed.length}</span>
      <span style={{ color: "#444" }}>Unchanged: {grouped.unchanged.length}</span>
    </div>
  );
}

function Group({ title, rows, accent }: { title: string; rows: Row[]; accent: string }) {
  if (rows.length === 0) return null;
  return (
    <section style={{ ...sectionStyle, borderTop: `4px solid ${accent}` }}>
      <h3 style={{ marginTop: 0 }}>
        {title} ({rows.length})
      </h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", color: "#666", fontSize: 13 }}>
            <th style={{ padding: "6px 8px" }}>Test case</th>
            <th style={{ padding: "6px 8px" }}>A</th>
            <th style={{ padding: "6px 8px" }}>→</th>
            <th style={{ padding: "6px 8px" }}>B</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.testCaseId} style={{ borderTop: "1px solid #eee" }}>
              <td style={{ padding: "8px" }}>{r.title}</td>
              <td style={{ padding: "8px" }}>
                {r.a ? <StatusPill status={r.a} /> : <em>—</em>}
              </td>
              <td style={{ padding: "8px", color: "#888" }}>→</td>
              <td style={{ padding: "8px" }}>
                {r.b ? <StatusPill status={r.b} /> : <em>—</em>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
