"use client";

import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, CheckCircle2, MoonStar, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useI18n } from "@/src/i18n/provider";
import { getSettings, updateSettings } from "@/src/lib/api/settings";
import { getCopilotStatus } from "@/src/lib/api/copilot";
import { API_URL } from "@/src/lib/constants";
import { useTheme } from "@/src/components/ui/theme-provider";

export default function SettingsPage() {
  const { locale } = useI18n();
  const { theme, setTheme } = useTheme();

  const settingsQuery = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: getSettings,
  });
  const statusQuery = useQuery({
    queryKey: ["copilot-status"],
    queryFn: getCopilotStatus,
    retry: 0,
  });
  const healthQuery = useQuery({
    queryKey: ["api-health"],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) {
        throw new Error("Backend unavailable");
      }
      return (await response.json()) as { status: string; service: string; version: string };
    },
    retry: 0,
  });
  const saveMutation = useMutation({
    mutationFn: updateSettings,
  });

  const settings = settingsQuery.data?.data;

  function persistSettings(next: { locale?: "ru" | "en"; theme?: "light" | "dark" }) {
    void saveMutation.mutateAsync({
      locale,
      theme,
      density: settings?.density ?? "comfortable",
      workspaceName: settings?.workspaceName ?? "Рабочее пространство StockPilot",
      ...next,
    });
  }

  const apiAvailable = healthQuery.data?.status === "ok";
  const ollamaStatus = statusQuery.data;

  return (
    <div className="space-y-7">
      <PageTitle
        title={locale === "ru" ? "Настройки" : "Settings"}
        description={
          locale === "ru"
            ? "Локальные параметры интерфейса и диагностика сервера/Ollama."
            : "Local interface preferences and backend/Ollama diagnostics."
        }
      />

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Surface className="p-6">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl bg-[color:var(--surface-muted)] p-2.5">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">
                {locale === "ru" ? "Локальный режим" : "Local-first mode"}
              </h2>
              <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                {locale === "ru"
                  ? "Данные и AI-ответы обрабатываются локально через сервер и Ollama. Внешние AI-провайдеры не используются."
                  : "Data and AI responses are processed locally through the backend and Ollama. External AI providers are not used."}
              </p>
            </div>
          </div>
        </Surface>

        <Surface className="p-6">
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">{locale === "ru" ? "Текущее окружение" : "Current environment"}</h2>
            <StatusRow
              icon={<Server className="h-4 w-4" />}
              label={locale === "ru" ? "API сервера" : "Backend API"}
              value={API_URL}
              state={apiAvailable ? "ok" : "warn"}
            />
            <StatusRow
              icon={<Bot className="h-4 w-4" />}
              label="Ollama"
              value={ollamaStatus?.message ?? (statusQuery.isLoading ? (locale === "ru" ? "Проверяем..." : "Checking...") : locale === "ru" ? "Нет ответа" : "No response")}
              state={ollamaStatus?.available ? "ok" : "warn"}
            />
            <StatusRow
              icon={<CheckCircle2 className="h-4 w-4" />}
              label={locale === "ru" ? "Текущая модель" : "Current model"}
              value={ollamaStatus?.model ?? "qwen2.5:7b"}
              state="neutral"
            />
          </div>
        </Surface>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Surface className="p-6">
          <div className="flex items-center gap-3">
            <MoonStar className="h-5 w-5 text-[color:var(--muted)]" />
            <div>
              <h2 className="text-base font-semibold">{locale === "ru" ? "Тема" : "Theme"}</h2>
              <p className="text-sm text-[color:var(--muted)]">
                {locale === "ru" ? "Тема сохраняется локально в браузере." : "The theme is stored locally in the browser."}
              </p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            {(["light", "dark"] as const).map((option) => (
              <UiButton
                key={option}
                variant={theme === option ? "primary" : "secondary"}
                onClick={() => {
                  setTheme(option);
                  persistSettings({ theme: option });
                }}
              >
                {option === "light"
                  ? locale === "ru"
                    ? "Светлая"
                    : "Light"
                  : locale === "ru"
                    ? "Тёмная"
                    : "Dark"}
              </UiButton>
            ))}
          </div>
        </Surface>
      </section>

      <Surface className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-base font-semibold">
              {locale === "ru" ? "Проверка подключения Ollama" : "Ollama connectivity check"}
            </h2>
            <p className="mt-1 text-sm text-[color:var(--muted)]">
              {locale === "ru"
                ? "Используйте кнопку, чтобы обновить статус локального AI-помощника."
                : "Use the button to refresh the local AI assistant status."}
            </p>
          </div>
          <UiButton
            variant="secondary"
            onClick={() => void statusQuery.refetch()}
            leadingIcon={<RefreshCw className="h-4 w-4" />}
            loading={statusQuery.isFetching}
          >
            {locale === "ru" ? "Проверить Ollama" : "Check Ollama"}
          </UiButton>
        </div>
      </Surface>
    </div>
  );
}

function StatusRow({
  icon,
  label,
  value,
  state,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  state: "ok" | "warn" | "neutral";
}) {
  const stateClass =
    state === "ok"
      ? "bg-[color:var(--success-soft)] text-[color:var(--success)]"
      : state === "warn"
        ? "bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
        : "bg-[color:var(--surface-muted)] text-[color:var(--muted)]";

  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-4 py-3">
      <div className="min-w-0">
        <div className="mb-1 flex items-center gap-2 text-sm font-medium">
          {icon}
          <span>{label}</span>
        </div>
        <p className="break-words text-sm text-[color:var(--muted)]">{value}</p>
      </div>
      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${stateClass}`}>
        {state === "ok" ? "OK" : state === "warn" ? "Проверить" : "Инфо"}
      </span>
    </div>
  );
}
