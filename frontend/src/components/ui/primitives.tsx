"use client";

import { m } from "framer-motion";
import { ChevronRight } from "lucide-react";
import type { ButtonHTMLAttributes, PropsWithChildren, ReactNode } from "react";

import { cn } from "@/src/lib/utils";

const badgeStyles: Record<string, string> = {
  critical:
    "bg-[color:var(--danger-soft)] text-[color:var(--danger)] ring-[color:var(--danger-soft)]",
  high: "bg-[color:var(--warning-soft)] text-[color:var(--warning)] ring-[color:var(--warning-soft)]",
  medium:
    "bg-[color:var(--accent-soft)] text-[color:var(--accent)] ring-[color:var(--accent-soft)]",
  low: "bg-[color:var(--surface-3)] text-[color:var(--muted-strong)] ring-[color:var(--line-strong)]",
  info:
    "bg-[color:var(--success-soft)] text-[color:var(--success)] ring-[color:var(--success-soft)]",
  urgent:
    "bg-[color:var(--danger-soft)] text-[color:var(--danger)] ring-[color:var(--danger-soft)]",
  planned:
    "bg-[color:var(--warning-soft)] text-[color:var(--warning)] ring-[color:var(--warning-soft)]",
  monitor:
    "bg-[color:var(--accent-soft)] text-[color:var(--accent)] ring-[color:var(--accent-soft)]",
  no_action:
    "bg-[color:var(--surface-3)] text-[color:var(--muted)] ring-[color:var(--line)]",
  high_confidence:
    "bg-[color:var(--success-soft)] text-[color:var(--success)] ring-[color:var(--success-soft)]",
  medium_confidence:
    "bg-[color:var(--warning-soft)] text-[color:var(--warning)] ring-[color:var(--warning-soft)]",
  low_confidence:
    "bg-[color:var(--danger-soft)] text-[color:var(--danger)] ring-[color:var(--danger-soft)]",
};

const buttonStyles: Record<string, string> = {
  primary:
    "bg-[color:var(--accent)] text-white hover:bg-[color:var(--accent-strong)] shadow-[var(--shadow-soft)]",
  secondary:
    "bg-[color:var(--surface-2)] text-[color:var(--text)] hover:bg-[color:var(--surface-3)] border border-[color:var(--line)]",
  ghost:
    "bg-transparent text-[color:var(--muted-strong)] hover:bg-[color:var(--surface-3)]",
  danger:
    "bg-[color:var(--danger)] text-white hover:brightness-110 shadow-[var(--shadow-soft)]",
};

export function Card({
  children,
  className = "",
  variant = "default",
}: PropsWithChildren<{
  className?: string;
  variant?: "default" | "strong" | "ghost" | "inverse";
}>) {
  const variantStyles: Record<string, string> = {
    default: "surface-panel",
    strong: "surface-panel-strong",
    ghost: "border border-[color:var(--line)] bg-[color:var(--surface-2)]",
    inverse:
      "border border-white/8 bg-[color:var(--surface-inverse)] text-white shadow-[var(--shadow-hard)]",
  };

  return (
    <section
      className={cn(
        "rounded-[var(--radius-panel)] p-5 md:p-6",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </section>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  compact = false,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 md:flex-row md:items-end md:justify-between",
        compact && "gap-2"
      )}
    >
      <div className={cn("space-y-2", compact && "space-y-1")}>
        {eyebrow ? (
          <div className="text-[11px] font-semibold uppercase text-[color:var(--accent)]">
            {eyebrow}
          </div>
        ) : null}
        <div className="space-y-1">
          <h2 className="text-[1.18rem] font-semibold text-[color:var(--text)] md:text-[1.4rem]">
            {title}
          </h2>
          {description ? (
            <p className="max-w-3xl text-sm leading-6 text-[color:var(--muted)]">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      {action}
    </div>
  );
}

export function Badge({
  label,
  tone = "info",
  icon,
}: {
  label: string;
  tone?: string;
  icon?: ReactNode;
}) {
  const style = badgeStyles[tone] ?? badgeStyles.info;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase ring-1",
        style
      )}
    >
      {icon}
      {label}
    </span>
  );
}

export function Button({
  children,
  className = "",
  variant = "primary",
  leading,
  trailing,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  className?: string;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  leading?: ReactNode;
  trailing?: ReactNode;
}) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-[1rem] px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-50",
        buttonStyles[variant],
        className
      )}
    >
      {leading}
      {children}
      {trailing}
    </button>
  );
}

export function MetricCard({
  label,
  value,
  hint,
  trend,
  status,
  accent = "accent",
  footer,
}: {
  label: string;
  value: string;
  hint?: string;
  trend?: string;
  status?: ReactNode;
  accent?: "accent" | "success" | "warning" | "danger";
  footer?: ReactNode;
}) {
  const accentBar: Record<string, string> = {
    accent: "from-[color:var(--accent)]/20 to-transparent",
    success: "from-[color:var(--success)]/20 to-transparent",
    warning: "from-[color:var(--warning)]/20 to-transparent",
    danger: "from-[color:var(--danger)]/20 to-transparent",
  };

  return (
    <m.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.34, ease: [0.2, 0.8, 0.2, 1] }}
      className={cn(
        "group relative overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--line)] bg-[color:var(--surface-1)] p-4 shadow-[var(--shadow-soft)]",
        "before:absolute before:inset-x-0 before:top-0 before:h-18 before:bg-gradient-to-b before:content-['']",
        accentBar[accent]
      )}
    >
      <div className="relative space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="text-[11px] font-semibold uppercase text-[color:var(--muted)]">
              {label}
            </div>
            <div className="kpi-value text-3xl font-semibold text-[color:var(--text)] md:text-[2rem]">
              {value}
            </div>
          </div>
          {status}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          {hint ? (
            <div className="text-sm leading-6 text-[color:var(--muted)]">{hint}</div>
          ) : null}
          {trend ? (
            <div className="rounded-full bg-[color:var(--surface-3)] px-3 py-1 text-xs font-medium text-[color:var(--muted-strong)]">
              {trend}
            </div>
          ) : null}
        </div>

        {footer}
      </div>
    </m.div>
  );
}

export function InlineMetric({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper?: string;
}) {
  return (
    <div className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-3">
      <div className="text-[11px] font-semibold uppercase text-[color:var(--muted)]">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold text-[color:var(--text)]">{value}</div>
      {helper ? (
        <div className="mt-1 text-xs leading-5 text-[color:var(--muted)]">{helper}</div>
      ) : null}
    </div>
  );
}

export function EyebrowPill({
  label,
  trailing,
}: {
  label: string;
  trailing?: ReactNode;
}) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--surface-2)] px-3 py-1.5 text-[11px] font-semibold uppercase text-[color:var(--muted-strong)]">
      {label}
      {trailing}
    </div>
  );
}

export function EmptyPanel({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="grid min-h-64 place-items-center">
      <div className="max-w-lg text-center">
        <div className="text-2xl font-semibold text-[color:var(--text)]">
          {title}
        </div>
        <p className="mt-3 text-sm leading-7 text-[color:var(--muted)]">{description}</p>
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </Card>
  );
}

export function LoadingPanel({ label }: { label: string }) {
  return (
    <Card className="space-y-4">
      <div className="shimmer h-4 w-44 rounded-full" />
      <div className="shimmer h-56 rounded-[1.2rem]" />
      <div className="text-sm text-[color:var(--muted)]">{label}</div>
    </Card>
  );
}

export function SurfaceList({
  items,
}: {
  items: Array<{ title: string; body: string; meta?: string }>;
}) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={`${item.title}-${item.meta ?? ""}`}
          className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-4"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="font-semibold text-[color:var(--text)]">{item.title}</div>
              <div className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                {item.body}
              </div>
            </div>
            {item.meta ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-[color:var(--muted)]">
                {item.meta}
                <ChevronRight className="h-3.5 w-3.5" />
              </span>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ProgressBar({
  value,
  tone = "accent",
}: {
  value: number;
  tone?: "accent" | "success" | "warning" | "danger";
}) {
  const width = `${Math.max(0, Math.min(value, 100))}%`;
  const toneStyles: Record<string, string> = {
    accent: "bg-[color:var(--accent)]",
    success: "bg-[color:var(--success)]",
    warning: "bg-[color:var(--warning)]",
    danger: "bg-[color:var(--danger)]",
  };

  return (
    <div className="h-2 overflow-hidden rounded-full bg-[color:var(--surface-3)]">
      <div
        className={cn("h-full rounded-full transition-all duration-500", toneStyles[tone])}
        style={{ width }}
      />
    </div>
  );
}

export function KeyValueRow({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[0.95rem] border border-[color:var(--line)] bg-[color:var(--surface-2)] px-3 py-2.5">
      <span className="text-sm text-[color:var(--muted)]">{label}</span>
      <span className="text-sm font-semibold text-[color:var(--text)]">{value}</span>
    </div>
  );
}

export function StatSurface({
  title,
  value,
  meta,
  icon,
}: {
  title: string;
  value: string;
  meta?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="rounded-[1rem] border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-4">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase text-[color:var(--muted)]">
        {icon}
        {title}
      </div>
      <div className="mt-2 text-xl font-semibold text-[color:var(--text)]">
        {value}
      </div>
      {meta ? (
        <div className="mt-2 text-xs leading-5 text-[color:var(--muted)]">{meta}</div>
      ) : null}
    </div>
  );
}
