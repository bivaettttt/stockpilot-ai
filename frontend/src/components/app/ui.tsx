"use client";

import Link from "next/link";
import { Loader2 } from "lucide-react";
import { cn } from "@/src/lib/utils";
import type { ButtonHTMLAttributes, PropsWithChildren, ReactNode } from "react";

export function AppContainer({ children }: PropsWithChildren) {
  return <div className="mx-auto w-full max-w-[1380px] px-4 md:px-7">{children}</div>;
}

export function Surface({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <section
      className={cn(
        "surface-panel rounded-[var(--radius-panel)]",
        className
      )}
    >
      {children}
    </section>
  );
}

export function PageTitle({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-1.5">
      <h1 className="text-[1.8rem] font-semibold md:text-[2.15rem]">{title}</h1>
      <p className="max-w-3xl text-sm leading-6 text-[color:var(--muted)]">{description}</p>
    </div>
  );
}

export function UiButton({
  href,
  children,
  variant = "primary",
  className,
  loading = false,
  leadingIcon,
  success = false,
  ...props
}: PropsWithChildren<{
  href?: string;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
  loading?: boolean;
  leadingIcon?: ReactNode;
  success?: boolean;
}> &
  ButtonHTMLAttributes<HTMLButtonElement>) {
  const styles = cn(
    "inline-flex h-10 items-center justify-center gap-2 rounded-2xl px-4 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]/45 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.985]",
    variant === "primary" &&
      "bg-[color:var(--accent)] text-white shadow-[var(--shadow-sm)] hover:-translate-y-px hover:shadow-[0_10px_24px_-16px_var(--accent)]",
    variant === "secondary" &&
      "border border-[color:var(--line)] bg-[color:var(--surface-2)] text-[color:var(--text)] hover:border-[color:var(--line-strong)] hover:bg-[color:var(--surface-3)]",
    variant === "ghost" && "text-[color:var(--muted)] hover:bg-[color:var(--surface-muted)] hover:text-[color:var(--text)]",
    success && "ring-1 ring-[color:var(--success)]/40",
    className
  );

  if (href) {
    return (
      <Link href={href} className={styles}>
        {leadingIcon}
        {children}
      </Link>
    );
  }

  return (
    <button {...props} className={styles} disabled={props.disabled || loading}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : leadingIcon}
      {children}
    </button>
  );
}
