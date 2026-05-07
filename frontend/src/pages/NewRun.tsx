import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../lib/api";

export function NewRunPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [promptId, setPromptId] = useState<number | "">("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [enableJudge, setEnableJudge] = useState(false);

  const [promptsQ, casesQ] = useQueries({
    queries: [
      { queryKey: ["prompt-templates"], queryFn: api.listPromptTemplates },
      { queryKey: ["test-cases"], queryFn: api.listTestCases },
    ],
  });

  const createRun = useMutation({
    mutationFn: api.createRun,
    onSuccess: (run) => {
      qc.invalidateQueries({ queryKey: ["runs"] });
      navigate(`/runs/${run.id}`);
    },
  });

  const toggle = (id: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const allCases = casesQ.data ?? [];
  const allSelected = allCases.length > 0 && selected.size === allCases.length;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof promptId !== "number") return;
    const ids = selected.size > 0 ? Array.from(selected) : allCases.map((c) => c.id);
    createRun.mutate({
      prompt_template_id: promptId,
      test_case_ids: ids,
      enable_llm_judge: enableJudge,
    });
  };

  return (
    <section>
      <h2>New evaluation run</h2>

      {(promptsQ.isLoading || casesQ.isLoading) && <p>Loading…</p>}
      {(promptsQ.error || casesQ.error) && (
        <pre style={{ color: "crimson" }}>
          {String(promptsQ.error ?? casesQ.error)}
        </pre>
      )}

      {promptsQ.data && casesQ.data && (
        <form onSubmit={submit} style={{ display: "grid", gap: 16, maxWidth: 720 }}>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Prompt template</span>
            <select
              value={promptId}
              onChange={(e) => setPromptId(e.target.value ? Number(e.target.value) : "")}
              required
            >
              <option value="">— select —</option>
              {promptsQ.data.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}@{p.version}
                </option>
              ))}
            </select>
          </label>

          <fieldset style={{ border: "1px solid #ddd", borderRadius: 6, padding: 12 }}>
            <legend>Test cases (none = all)</legend>
            <label style={{ display: "block", marginBottom: 8 }}>
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() =>
                  setSelected(allSelected ? new Set() : new Set(allCases.map((c) => c.id)))
                }
              />{" "}
              select all
            </label>
            <div style={{ display: "grid", gap: 4 }}>
              {allCases.map((c) => (
                <label key={c.id} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                  <input
                    type="checkbox"
                    checked={selected.has(c.id)}
                    onChange={() => toggle(c.id)}
                  />
                  <span>
                    <strong>{c.title}</strong>{" "}
                    <span style={{ color: "#666", fontSize: 12 }}>
                      [{c.tags.join(", ")}]
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <label
            style={{
              display: "flex",
              gap: 8,
              alignItems: "flex-start",
              padding: 12,
              border: "1px dashed #ccc",
              borderRadius: 6,
            }}
          >
            <input
              type="checkbox"
              checked={enableJudge}
              onChange={(e) => setEnableJudge(e.target.checked)}
              style={{ marginTop: 4 }}
            />
            <span>
              <strong>Run LLM-as-judge</strong> after deterministic checks (one extra
              model call per case). Judge verdict is recorded with severity{" "}
              <code>info</code> so it never overrides deterministic checks or human
              review — it's a parallel signal, not a tiebreaker.
            </span>
          </label>

          <button
            type="submit"
            disabled={createRun.isPending || promptId === ""}
            style={{
              padding: "8px 16px",
              background: "#3b5bdb",
              color: "white",
              border: 0,
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            {createRun.isPending ? "Running…" : "Run evaluation"}
          </button>

          {createRun.error && (
            <pre style={{ color: "crimson" }}>{String(createRun.error)}</pre>
          )}
        </form>
      )}
    </section>
  );
}
