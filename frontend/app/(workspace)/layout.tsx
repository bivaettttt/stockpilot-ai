"use client";

import type { PropsWithChildren } from "react";
import { AnimatePresence, m } from "framer-motion";
import { usePathname } from "next/navigation";
import { AppShell } from "@/src/components/app/app-shell";
import { DashboardStateProvider } from "@/src/components/app/dashboard-state-provider";

export default function WorkspaceLayout({ children }: PropsWithChildren) {
  const pathname = usePathname();

  return (
    <DashboardStateProvider>
      <AppShell>
        <AnimatePresence mode="wait">
          <m.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            {children}
          </m.div>
        </AnimatePresence>
      </AppShell>
    </DashboardStateProvider>
  );
}
