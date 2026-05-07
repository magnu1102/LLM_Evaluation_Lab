export type Status = "pass" | "fail" | "needs_review";

export interface ExpectedBehavior {
  must_include: string[];
  must_not_include: string[];
  requires_citation: boolean;
  must_refuse: boolean;
  min_chars: number | null;
  max_chars: number | null;
}

export interface TestCase {
  id: number;
  title: string;
  context: string;
  question: string;
  expected_behavior: ExpectedBehavior;
  tags: string[];
  created_at: string;
}

export interface PromptTemplate {
  id: number;
  name: string;
  version: number;
  system_prompt: string;
  user_template: string;
  notes: string;
  created_at: string;
}

export interface CheckOutcome {
  criterion: string;
  severity: string;
  passed: boolean;
  detail: string;
}

export interface Result {
  id: number;
  run_id: number;
  test_case_id: number;
  model_output: string;
  latency_ms: number;
  automatic_checks: CheckOutcome[];
  human_rating: Status | null;
  human_notes: string;
  status: Status;
}

export interface RunSummary {
  total: number;
  passed: number;
  failed: number;
  needs_review: number;
}

export interface Run {
  id: number;
  prompt_template_id: number;
  provider: string;
  model: string;
  started_at: string;
  finished_at: string | null;
  summary: RunSummary;
  results: Result[];
}
