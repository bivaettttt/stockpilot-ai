"use client";

import { createContext, useContext, useSyncExternalStore, type PropsWithChildren } from "react";
import { useStockpilotDashboard, type DashboardState } from "@/src/hooks/use-stockpilot-dashboard";

const DashboardStateContext = createContext<DashboardState | null>(null);
const noopSubscribe = () => () => {};

export function DashboardStateProvider({ children }: PropsWithChildren) {
  const state = useStockpilotDashboard();
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);

  if (!mounted) {
    return (
      <DashboardStateContext.Provider value={state}>
        <div className="grid min-h-screen place-items-center bg-[color:var(--background)] text-[color:var(--text)]">
          <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface)] px-5 py-4 text-sm text-[color:var(--muted)] shadow-[var(--shadow-soft)]">
            Загрузка рабочего пространства...
          </div>
        </div>
      </DashboardStateContext.Provider>
    );
  }

  return <DashboardStateContext.Provider value={state}>{children}</DashboardStateContext.Provider>;
}

export function useDashboardState() {
  const context = useContext(DashboardStateContext);
  if (!context) {
    throw new Error("useDashboardState must be used inside DashboardStateProvider");
  }
  return context;
}
