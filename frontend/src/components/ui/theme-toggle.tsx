"use client";

import { MoonStar, SunMedium } from "lucide-react";

import { useTheme } from "@/src/components/ui/theme-provider";
import { useI18n } from "@/src/i18n/provider";
import { cn } from "@/src/lib/utils";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const { t } = useI18n();

  return (
    <button
      type="button"
      aria-label={theme === "dark" ? t("theme.to_light") : t("theme.to_dark")}
      aria-pressed={theme === "dark"}
      onClick={toggleTheme}
      className={cn(
        "group relative inline-flex h-9 w-16 items-center rounded-full border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-1 text-[color:var(--text)] shadow-[var(--shadow-sm)] transition duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--ring)]",
        className
      )}
    >
      <span
        className={cn(
          "absolute top-1 flex h-7 w-7 items-center justify-center rounded-full bg-[color:var(--surface)] shadow-[var(--shadow-sm)] transition duration-300",
          theme === "dark" ? "translate-x-7" : "translate-x-0"
        )}
      >
        {theme === "dark" ? (
          <MoonStar className="h-4 w-4 text-[color:var(--text)]" />
        ) : (
          <SunMedium className="h-4 w-4 text-[color:var(--text)]" />
        )}
      </span>

      <span className="sr-only">{theme === "dark" ? "Тёмная тема" : "Светлая тема"}</span>
      <span className="flex w-full items-center justify-between px-1.5 text-[9px] font-semibold uppercase text-[color:var(--muted)]">
        <span>С</span>
        <span>Т</span>
      </span>
    </button>
  );
}
