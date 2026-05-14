"use client";

import { Command } from "cmdk";
import { AnimatePresence, m } from "framer-motion";
import { Clock3, Search } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useI18n } from "@/src/i18n/provider";

const ROUTES = [
  "overview",
  "analytics",
  "planning",
  "suppliers",
  "forecasting",
  "exceptions",
  "reliability",
  "segments",
  "reports",
  "history",
  "copilot",
  "settings",
] as const;

const RECENT_STORAGE_KEY = "stockpilot-recent-actions";

export function GlobalCommandMenu() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [recent, setRecent] = useState<string[]>(() => {
    if (typeof window === "undefined") return [];
    const parsed = JSON.parse(window.localStorage.getItem(RECENT_STORAGE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.slice(0, 5) : [];
  });
  const router = useRouter();
  const pathname = usePathname();
  const { t } = useI18n();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    function openCommand() {
      setOpen(true);
    }
    window.addEventListener("stockpilot-open-command", openCommand);
    return () => window.removeEventListener("stockpilot-open-command", openCommand);
  }, []);

  function navigateTo(route: string) {
    setOpen(false);
    setSearch("");
    router.push(`/${route}`);
    const nextRecent = [route, ...recent.filter((item) => item !== route)].slice(0, 5);
    setRecent(nextRecent);
    window.localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(nextRecent));
    toast.success(`${t("search.opened")} ${t(`nav.${route}`)}`);
  }

  const suggestions = useMemo(
    () => ROUTES.filter((route) => route !== pathname.replace("/", "")).slice(0, 3),
    [pathname]
  );

  return (
    <AnimatePresence>
      {open ? (
        <m.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[70] bg-black/20 p-4 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <m.div
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            className="mx-auto mt-16 w-full max-w-xl overflow-hidden rounded-xl border border-[color:var(--border)] bg-[color:var(--surface)] shadow-[var(--shadow-md)]"
            onClick={(e) => e.stopPropagation()}
          >
            <Command shouldFilter value={search} onValueChange={setSearch} className="w-full">
              <div className="flex items-center gap-2 border-b border-[color:var(--border)] px-3">
                <Search className="h-4 w-4 text-[color:var(--muted)]" />
                <Command.Input
                  autoFocus
                  placeholder={t("search.placeholder")}
                  className="h-11 w-full bg-transparent text-sm outline-none"
                />
              </div>
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Empty className="px-2 py-6 text-center text-sm text-[color:var(--muted)]">
                  {t("search.no_results")}
                </Command.Empty>

                {recent.length > 0 ? (
                  <Command.Group heading={t("search.recent")} className="px-1 pb-2 text-xs text-[color:var(--muted)]">
                    {recent.map((route) => (
                      <Command.Item
                        key={`recent-${route}`}
                        value={`recent ${route}`}
                        onSelect={() => navigateTo(route)}
                        className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm aria-selected:bg-[color:var(--surface-muted)]"
                      >
                        <Clock3 className="h-3.5 w-3.5 text-[color:var(--muted)]" />
                        {t(`nav.${route}`)}
                      </Command.Item>
                    ))}
                  </Command.Group>
                ) : null}

                <Command.Group heading={t("search.pages")} className="px-1 pb-2 text-xs text-[color:var(--muted)]">
                  {ROUTES.map((route) => (
                    <Command.Item
                      key={route}
                      value={`page ${route}`}
                      onSelect={() => navigateTo(route)}
                      className="cursor-pointer rounded-md px-2 py-2 text-sm aria-selected:bg-[color:var(--surface-muted)]"
                    >
                      {t(`nav.${route}`)}
                    </Command.Item>
                  ))}
                </Command.Group>

                <Command.Group heading={t("search.suggestions")} className="px-1 text-xs text-[color:var(--muted)]">
                  {suggestions.map((route) => (
                    <Command.Item
                      key={`suggestion-${route}`}
                      value={`suggestion ${route}`}
                      onSelect={() => navigateTo(route)}
                      className="cursor-pointer rounded-md px-2 py-2 text-sm aria-selected:bg-[color:var(--surface-muted)]"
                    >
                      {t("search.go_to")} {t(`nav.${route}`)}
                    </Command.Item>
                  ))}
                </Command.Group>
              </Command.List>
            </Command>
          </m.div>
        </m.div>
      ) : null}
    </AnimatePresence>
  );
}
