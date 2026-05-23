"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { m } from "framer-motion";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  CircleAlert,
  ClipboardList,
  Boxes,
  Building2,
  LayoutGrid,
  Menu,
  ScanSearch,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { useMemo, useState, useSyncExternalStore, type ComponentType, type PropsWithChildren } from "react";
import { ThemeToggle } from "@/src/components/ui/theme-toggle";
import { GlobalCommandMenu } from "@/src/components/app/global-command-menu";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { useI18n } from "@/src/i18n/provider";
import { cn } from "@/src/lib/utils";
import { AppContainer } from "@/src/components/app/ui";
import { formatDateTime } from "@/src/lib/format";
import { getCopilotStatus } from "@/src/lib/api/copilot";

const navGroups: Array<Array<{ key: string; icon: ComponentType<{ className?: string }> }>> = [
  [
    { key: "overview", icon: LayoutGrid },
    { key: "planning", icon: ClipboardList },
    { key: "suppliers", icon: Building2 },
  ],
  [
    { key: "analytics", icon: Boxes },
    { key: "forecasting", icon: Sparkles },
    { key: "exceptions", icon: CircleAlert },
    { key: "reliability", icon: ShieldCheck },
    { key: "segments", icon: ScanSearch },
    { key: "reports", icon: ClipboardList },
    { key: "history", icon: BarChart3 },
  ],
  [
    { key: "copilot", icon: Bot },
    { key: "settings", icon: Settings },
  ],
];

const noopSubscribe = () => () => {};

export function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const { t } = useI18n();
  const dashboard = useDashboardState();
  const statusQuery = useQuery({
    queryKey: ["copilot-status"],
    queryFn: getCopilotStatus,
    retry: 0,
    staleTime: 30_000,
  });

  const breadcrumb = useMemo(() => {
    const page = pathname.split("/").filter(Boolean).at(-1) ?? "overview";
    return [t("shell.workspace"), t(`nav.${page}`)];
  }, [pathname, t]);

  return (
    <div className="min-h-screen bg-[color:var(--background)] text-[color:var(--text)]">
      <div className="flex">
        <aside
          className={cn(
            "fixed inset-y-0 z-50 w-72 border-r border-[color:var(--line)] bg-[color:var(--surface)]/86 p-3 shadow-[var(--shadow-soft)] backdrop-blur-2xl transition md:sticky md:top-0 md:w-64 md:translate-x-0",
            open ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="mb-5 flex items-center justify-between rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-3 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-[color:var(--accent)] text-sm font-semibold text-white">
                SP
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">StockPilot AI</p>
                <p className="truncate text-xs text-[color:var(--muted)]">{t("shell.product")}</p>
              </div>
            </div>
            <button onClick={() => setOpen(false)} className="md:hidden">
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="space-y-4">
            {navGroups.map((group, index) => (
              <div key={index} className={cn(index > 0 && "border-t border-[color:var(--line)] pt-4")}>
                <p className="mb-2 px-2 text-[11px] font-semibold uppercase text-[color:var(--muted)]">
                  {index === 0
                    ? t("shell.group.core")
                    : index === 1
                      ? t("shell.group.analysis")
                      : t("shell.group.system")}
                </p>
                {group.map((item) => {
                  const href = `/${item.key}`;
                  const active = pathname === href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.key}
                      href={href}
                      className={cn(
                        "relative mb-1 flex items-center gap-2.5 rounded-2xl px-3 py-2.5 text-sm transition-all duration-200",
                        active
                          ? "bg-[color:var(--accent-soft)] text-[color:var(--text)] shadow-[var(--shadow-sm)]"
                          : "text-[color:var(--muted)] hover:bg-[color:var(--surface-2)] hover:text-[color:var(--text)]"
                      )}
                    >
                      {active ? (
                        <m.span
                          layoutId="active-nav-indicator"
                          transition={{ type: "spring", bounce: 0.25, duration: 0.45 }}
                          className="absolute inset-y-2 left-1 w-1 rounded-full bg-[color:var(--accent)]"
                        />
                      ) : null}
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{t(`nav.${item.key}`)}</span>
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>
        </aside>

        <div className="w-full min-w-0">
          <header className="sticky top-0 z-40 border-b border-[color:var(--line)] bg-[color:var(--background)]/78 backdrop-blur-2xl">
            <AppContainer>
              <div className="flex min-h-16 items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <button onClick={() => setOpen(true)} className="rounded-2xl border border-[color:var(--line)] p-2 md:hidden">
                    <Menu className="h-5 w-5" />
                  </button>
                  <div className="min-w-0">
                    <p className="truncate text-xs text-[color:var(--muted)]">
                      {breadcrumb[0]} / {breadcrumb[1]}
                    </p>
                    <p className="truncate text-sm font-medium">{t("shell.workspace_name")}</p>
                    {mounted && dashboard.result ? (
                      <p className="truncate text-xs text-[color:var(--muted)]">
                        {t("shell.active_analysis")}: {dashboard.activeAnalysisFilename ?? t("common.no_data")}
                        {dashboard.activeAnalysisCreatedAt
                          ? ` · ${formatDateTime(dashboard.activeAnalysisCreatedAt)}`
                          : ""}
                        {dashboard.isDemoAnalysis ? ` · ${t("shell.demo_data")}` : ""}
                        {dashboard.isHistoryAnalysis ? ` · ${t("shell.from_history")}` : ""}
                      </p>
                    ) : null}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="hidden items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-xs text-[color:var(--muted)] lg:flex">
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full",
                        statusQuery.data?.available ? "bg-[color:var(--success)]" : "bg-[color:var(--warning)]"
                      )}
                    />
                    {statusQuery.data?.available ? t("shell.ai_online") : t("shell.ai_check")}
                  </div>
                  <button
                    className="hidden h-10 items-center gap-2 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface)] px-3 text-sm text-[color:var(--muted)] md:flex"
                    onClick={() => window.dispatchEvent(new Event("stockpilot-open-command"))}
                  >
                    <Search className="h-4 w-4" />
                    {t("common.search")}
                  </button>
                  <ThemeToggle />
                </div>
              </div>
            </AppContainer>
          </header>

          <main className="min-w-0 py-8 md:py-10">
            <AppContainer>{children}</AppContainer>
          </main>
        </div>
      </div>
      <GlobalCommandMenu />
    </div>
  );
}
