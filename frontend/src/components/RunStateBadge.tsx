import type { RunState } from "../types";

const COLORS: Record<RunState, { bg: string; fg: string }> = {
  pending: { bg: "#e2e3e5", fg: "#383d41" },
  running: { bg: "#cce5ff", fg: "#004085" },
  completed: { bg: "#d4edda", fg: "#155724" },
  failed: { bg: "#f8d7da", fg: "#721c24" },
};

const LABELS: Record<RunState, string> = {
  pending: "pending",
  running: "running…",
  completed: "completed",
  failed: "failed",
};

export function RunStateBadge({ state }: { state: RunState }) {
  const c = COLORS[state] ?? COLORS.completed;
  return (
    <span
      style={{
        background: c.bg,
        color: c.fg,
        padding: "2px 8px",
        borderRadius: 12,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {LABELS[state] ?? state}
    </span>
  );
}

export function isTerminal(state: RunState): boolean {
  return state === "completed" || state === "failed";
}
