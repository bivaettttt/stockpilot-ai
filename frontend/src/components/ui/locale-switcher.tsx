"use client";

import { Globe } from "lucide-react";

import { useI18n } from "@/src/i18n/provider";

export function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <label className="inline-flex h-9 items-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-2.5">
      <Globe className="h-4 w-4 text-[color:var(--muted)]" />
      <select
        aria-label={t("shell.locale")}
        value={locale}
        onChange={(event) => setLocale(event.target.value as "ru" | "en")}
        className="bg-transparent text-xs font-medium uppercase text-[color:var(--text)] outline-none"
      >
        <option value="ru">RU</option>
        <option value="en">EN</option>
      </select>
    </label>
  );
}
