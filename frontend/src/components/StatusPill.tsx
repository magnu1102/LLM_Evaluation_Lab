import type { Status } from "../types";

const COLORS: Record<Status, { bg: string; fg: string }> = {
  pass: { bg: "#d4edda", fg: "#155724" },
  fail: { bg: "#f8d7da", fg: "#721c24" },
  needs_review: { bg: "#fff3cd", fg: "#856404" },
};

const LABELS: Record<Status, string> = {
  pass: "pass",
  fail: "fail",
  needs_review: "needs review",
};

export function StatusPill({ status }: { status: Status }) {
  const c = COLORS[status];
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
      {LABELS[status]}
    </span>
  );
}
