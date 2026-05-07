import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Layout } from "../components/Layout";
import { DashboardPage } from "../pages/Dashboard";
import { RunDetailPage } from "../pages/RunDetail";
import { TrendsPage } from "../pages/Trends";

type Json = Record<string, unknown> | unknown[];

function withProviders(initialPath: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="runs/:id" element={<RunDetailPage />} />
            <Route path="trends" element={<TrendsPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const originalFetch = globalThis.fetch;

function mockFetch(routes: Record<string, Json>) {
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const path = url.replace(/^https?:\/\/[^/]+/, "");
    const key = `${init?.method ?? "GET"} ${path}`;
    if (key in routes) {
      return new Response(JSON.stringify(routes[key]), { status: 200 });
    }
    return new Response("not found", { status: 404 });
  }) as unknown as typeof fetch;
}

beforeEach(() => mockFetch({}));
afterEach(() => {
  globalThis.fetch = originalFetch;
});

describe("Trends", () => {
  it("groups runs by prompt name@version with a status strip", async () => {
    mockFetch({
      "GET /runs": [
        {
          id: 1,
          prompt_template_id: 1,
          provider: "mock",
          model: "mock-1",
          started_at: "2026-05-01T10:00:00Z",
          finished_at: "2026-05-01T10:00:01Z",
          summary: { total: 5, passed: 4, failed: 1, needs_review: 0 },
          results: [],
        },
        {
          id: 2,
          prompt_template_id: 1,
          provider: "mock",
          model: "mock-1",
          started_at: "2026-05-02T10:00:00Z",
          finished_at: "2026-05-02T10:00:01Z",
          summary: { total: 5, passed: 5, failed: 0, needs_review: 0 },
          results: [],
        },
      ],
      "GET /prompt-templates": [
        {
          id: 1,
          name: "grounded-summarizer",
          version: 2,
          system_prompt: "",
          user_template: "",
          notes: "",
          created_at: "2026-04-30T00:00:00Z",
        },
      ],
    });
    render(withProviders("/trends"));
    expect(await screen.findByText(/grounded-summarizer@2/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/2 runs/)).toBeInTheDocument();
      expect(screen.getByText(/latest pass rate 100%/)).toBeInTheDocument();
    });
  });
});

describe("Dashboard", () => {
  it("renders the empty state when there are no runs", async () => {
    mockFetch({
      "GET /runs": [],
      "GET /prompt-templates": [],
    });
    render(withProviders("/"));
    expect(await screen.findByText(/Recent runs/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/No runs yet/)).toBeInTheDocument();
    });
  });
});

describe("RunDetail", () => {
  it("submits a review via PATCH /results/:id/review", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      calls.push({ url, init });
      const path = url.replace(/^https?:\/\/[^/]+/, "");
      const method = init?.method ?? "GET";

      if (method === "GET" && path === "/runs/1") {
        return new Response(
          JSON.stringify({
            id: 1,
            prompt_template_id: 1,
            provider: "mock",
            model: "mock-1",
            started_at: new Date().toISOString(),
            finished_at: new Date().toISOString(),
            summary: { total: 1, passed: 0, failed: 0, needs_review: 1 },
            results: [
              {
                id: 42,
                run_id: 1,
                test_case_id: 1,
                model_output: "hello",
                latency_ms: 1,
                automatic_checks: [
                  { criterion: "non_empty", severity: "fail", passed: true, detail: "" },
                ],
                human_rating: null,
                human_notes: "",
                status: "needs_review",
              },
            ],
          }),
          { status: 200 },
        );
      }
      if (method === "GET" && path === "/test-cases") {
        return new Response(JSON.stringify([]), { status: 200 });
      }
      if (method === "PATCH" && path === "/results/42/review") {
        return new Response(
          JSON.stringify({
            id: 42,
            run_id: 1,
            test_case_id: 1,
            model_output: "hello",
            latency_ms: 1,
            automatic_checks: [],
            human_rating: "pass",
            human_notes: "looks fine",
            status: "pass",
          }),
          { status: 200 },
        );
      }
      return new Response("not found", { status: 404 });
    }) as unknown as typeof fetch;

    const { container } = render(withProviders("/runs/1"));

    const passRadio = await screen.findByLabelText(/^\s*pass\s*$/);
    passRadio.click();

    const textarea = container.querySelector("textarea")!;
    textarea.focus();
    (textarea as HTMLTextAreaElement).value = "looks fine";
    textarea.dispatchEvent(new Event("input", { bubbles: true }));

    const saveBtn = screen.getByRole("button", { name: /save review/i });
    saveBtn.click();

    await waitFor(() => {
      expect(
        calls.some(
          (c) => c.url.endsWith("/results/42/review") && c.init?.method === "PATCH",
        ),
      ).toBe(true);
    });
  });
});
