"use client";

import { useSyncExternalStore, type PropsWithChildren } from "react";
import { cn } from "@/src/lib/utils";

const noopSubscribe = () => () => {};

export function ChartShell({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);

  return (
    <div className={cn("w-full min-w-0", className)}>
      {mounted ? (
        children
      ) : (
        <div
          aria-hidden="true"
          className="h-full w-full rounded-lg bg-[color:var(--surface-muted)]/80"
        />
      )}
    </div>
  );
}
