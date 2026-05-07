import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { api, TEST_CASE_EXPORT_URLS } from "../lib/api";

interface ImportResult {
  created: number;
  updated: number;
  errors: { index: number; error: string }[];
}

const card = {
  border: "1px solid #e5e5e5",
  borderRadius: 8,
  padding: 16,
  background: "#fff",
} as const;

export function TestCasesPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [lastImport, setLastImport] = useState<ImportResult | null>(null);

  const casesQ = useQuery({ queryKey: ["test-cases"], queryFn: api.listTestCases });

  const importMut = useMutation({
    mutationFn: (file: File) => api.importTestCases(file),
    onSuccess: (data) => {
      setLastImport(data);
      qc.invalidateQueries({ queryKey: ["test-cases"] });
      if (fileRef.current) fileRef.current.value = "";
    },
  });

  const onUpload = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    importMut.mutate(file);
  };

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <h2>Test cases</h2>
      <p style={{ color: "#555", marginTop: -8 }}>
        The dataset under evaluation. Round-trips with{" "}
        <code>eval/test_cases.yaml</code>: download what's in the database, edit
        it, and upload it back.
      </p>

      <article style={card}>
        <h3 style={{ marginTop: 0 }}>Export</h3>
        <p style={{ marginTop: 0, color: "#555" }}>
          Same shape as the seed YAML, sorted by id.
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <a href={TEST_CASE_EXPORT_URLS.yaml}>⬇ test_cases.yaml</a>
          <a href={TEST_CASE_EXPORT_URLS.json}>⬇ test_cases.json</a>
        </div>
      </article>

      <article style={card}>
        <h3 style={{ marginTop: 0 }}>Import</h3>
        <p style={{ marginTop: 0, color: "#555" }}>
          Upload a YAML or JSON file with a top-level <code>cases</code> list.
          Existing cases are matched by <code>title</code> and updated; unknown
          titles are inserted. Per-entry validation errors are reported below;
          valid entries in the same upload still commit.
        </p>
        <form onSubmit={onUpload} style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input ref={fileRef} type="file" accept=".yaml,.yml,.json,application/x-yaml,application/json,text/yaml" />
          <button
            type="submit"
            disabled={importMut.isPending}
            style={{
              padding: "6px 12px",
              background: "#3b5bdb",
              color: "white",
              border: 0,
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            {importMut.isPending ? "Uploading…" : "Import"}
          </button>
        </form>

        {importMut.error && (
          <pre style={{ color: "crimson", marginTop: 12 }}>{String(importMut.error)}</pre>
        )}
        {lastImport && (
          <div style={{ marginTop: 12 }}>
            <p style={{ margin: 0 }}>
              Created {lastImport.created} · Updated {lastImport.updated}
              {lastImport.errors.length > 0 && (
                <> · <span style={{ color: "#856404" }}>{lastImport.errors.length} error(s)</span></>
              )}
            </p>
            {lastImport.errors.length > 0 && (
              <ul style={{ marginTop: 8 }}>
                {lastImport.errors.map((e) => (
                  <li key={e.index} style={{ color: "#721c24" }}>
                    entry #{e.index}: {e.error}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </article>

      <article style={card}>
        <h3 style={{ marginTop: 0 }}>Current dataset</h3>
        {casesQ.isLoading && <p>Loading…</p>}
        {casesQ.error && <pre style={{ color: "crimson" }}>{String(casesQ.error)}</pre>}
        {casesQ.data && casesQ.data.length === 0 && <p>No test cases yet.</p>}
        {casesQ.data && casesQ.data.length > 0 && (
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {casesQ.data.map((c) => (
              <li key={c.id} style={{ marginBottom: 6 }}>
                <strong>{c.title}</strong>
                {c.tags.length > 0 && (
                  <span style={{ color: "#666", fontSize: 12 }}> [{c.tags.join(", ")}]</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </article>
    </section>
  );
}
