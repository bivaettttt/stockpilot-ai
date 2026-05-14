"use client";

import type { ReactNode } from "react";

export const chartAxisTick = { fill: "var(--chart-axis)", fontSize: 12 };
export const chartGridStroke = "var(--chart-grid)";

export const chartTooltipStyle = {
  background: "var(--chart-tooltip-bg)",
  border: "1px solid var(--line)",
  borderRadius: "14px",
  color: "var(--text)",
  boxShadow: "var(--shadow-medium)",
} as const;

export function ChartTooltipCard({
  title,
  children,
}: {
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-[0.95rem] border border-[color:var(--line)] bg-[color:var(--chart-tooltip-bg)] px-3 py-2.5 shadow-[var(--shadow-medium)]">
      {title ? <div className="text-[11px] font-semibold uppercase text-[color:var(--muted)]">{title}</div> : null}
      <div className="mt-1 space-y-1">{children}</div>
    </div>
  );
}
