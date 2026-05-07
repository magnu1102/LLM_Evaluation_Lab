import type { PromptTemplate, Result, Run, Status, TestCase } from "../types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`${resp.status} ${resp.statusText}: ${text || path}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  health: () => request<{ status: string; db: boolean; provider: string }>("/health"),
  listTestCases: () => request<TestCase[]>("/test-cases"),
  listPromptTemplates: () => request<PromptTemplate[]>("/prompt-templates"),
  listRuns: () => request<Run[]>("/runs"),
  getRun: (id: number) => request<Run>(`/runs/${id}`),
  createRun: (body: {
    prompt_template_id: number;
    test_case_ids: number[];
    model?: string;
    enable_llm_judge?: boolean;
  }) => request<Run>("/runs", { method: "POST", body: JSON.stringify(body) }),
  reviewResult: (id: number, body: { human_rating: Status | null; human_notes: string }) =>
    request<Result>(`/results/${id}/review`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
};
