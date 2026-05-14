"use client";

import { AlertTriangle, ArrowRight, CheckCircle2, ShieldAlert, Signal } from "lucide-react";
import Link from "next/link";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { formatNumber, formatRisk } from "@/src/lib/format";
import { cn } from "@/src/lib/utils";

export default function ExceptionsPage() {
  const state = useDashboardState();
  const queue = state.advancedRiskQueue;
  const highRisk = queue.filter((item) => item.urgency_level === "critical" || item.urgency_level === "high");
  const mediumRisk = queue.filter((item) => item.urgency_level === "medium");
  const weakForecast = queue.filter((item) => item.weak_forecast);

  if (!state.result) {
    return (
      <div className="space-y-6">
        <PageTitle title="Риски" description="Очередь дефицита, аномалий и SKU, которые требуют внимания." />
        <Surface className="p-6 md:p-7">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <ShieldAlert className="h-4 w-4" />
              Анализ ещё не запущен
            </div>
            <h2 className="text-2xl font-semibold">Риски появятся после анализа</h2>
            <p className="text-sm leading-6 text-[color:var(--muted)]">
              StockPilot проверит риск дефицита, слабую надёжность прогноза, нестабильный спрос и исключения по текущему файлу.
            </p>
            <UiButton href="/overview#upload-panel">Загрузить файл</UiButton>
          </div>
        </Surface>
      </div>
    );
  }

  if (queue.length === 0 || highRisk.length === 0 && mediumRisk.length === 0) {
    return (
      <div className="space-y-6">
        <PageTitle title="Риски" description="Очередь дефицита, аномалий и SKU, которые требуют внимания." />
        <Surface className="p-6 md:p-7">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--success-soft)] px-3 py-1.5 text-sm text-[color:var(--success)]">
              <CheckCircle2 className="h-4 w-4" />
              Критичных рисков не найдено
            </div>
            <h2 className="text-2xl font-semibold">По текущему анализу нет срочной очереди рисков</h2>
            <p className="text-sm leading-6 text-[color:var(--muted)]">
              Проверены риск дефицита, риск избытка, слабая надёжность прогноза и нестабильный спрос. Для деталей откройте закупочный план и надёжность анализа.
            </p>
            <div className="flex flex-wrap gap-2.5">
              <UiButton href="/planning">Открыть закупочный план</UiButton>
              <UiButton href="/reliability" variant="secondary">Надёжность анализа</UiButton>
            </div>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageTitle title="Риски" description="Рабочая очередь SKU, которые стоит проверить перед закупкой." />

      <section className="grid gap-4 md:grid-cols-3">
        <RiskSummary title="Высокий приоритет" value={formatNumber(highRisk.length, 0)} tone="danger" />
        <RiskSummary title="Средний приоритет" value={formatNumber(mediumRisk.length, 0)} tone="warning" />
        <RiskSummary title="Слабая надёжность прогноза" value={formatNumber(weakForecast.length, 0)} tone="accent" />
      </section>

      <Surface className="overflow-hidden p-0">
        <div className="border-b border-[color:var(--line)] px-5 py-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold">Очередь рисков</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">Сначала показаны SKU с максимальным операционным риском.</p>
            </div>
            <UiButton href="/planning" variant="secondary">Перейти к решениям</UiButton>
          </div>
        </div>
        <div className="divide-y divide-[color:var(--line)]">
          {queue.slice(0, 30).map((item) => (
            <Link
              key={item.sku}
              href="/planning"
              className="grid gap-4 px-5 py-4 transition hover:bg-[color:var(--table-row-hover)] md:grid-cols-[1fr_11rem_11rem_auto]"
            >
              <div className="min-w-0">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="font-semibold">{item.sku}</span>
                  <SeverityBadge level={item.urgency_level} />
                  {item.weak_forecast ? (
                    <span className="rounded-full bg-[color:var(--warning-soft)] px-2.5 py-1 text-xs text-[color:var(--warning)]">
                      проверить прогноз
                    </span>
                  ) : null}
                </div>
                <p className="break-words text-sm font-medium">{item.product_name}</p>
                <p className="mt-1 line-clamp-2 text-sm text-[color:var(--muted)]">{item.message || item.explanation || "Проверьте остаток, спрос и рекомендацию по закупке."}</p>
              </div>
              <RiskMetric label="Риск дефицита" value={formatRisk(item.stockout_risk ?? 0)} />
              <RiskMetric label="Остаток" value={formatNumber(item.current_stock, 0)} />
              <div className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
                <span>Открыть</span>
                <ArrowRight className="h-4 w-4" />
              </div>
            </Link>
          ))}
        </div>
      </Surface>

      <section className="grid gap-4 md:grid-cols-3">
        <SignalCard title="Что проверяется" body="Дефицит, избыток, нестабильный спрос, слабая надёжность прогноза и операционный приоритет SKU." icon={<Signal className="h-5 w-5" />} />
        <SignalCard title="Как действовать" body="Откройте закупочный план, проверьте детали SKU, скорректируйте итоговое количество и оставьте комментарий." icon={<AlertTriangle className="h-5 w-5" />} />
        <SignalCard title="Что не делаем" body="StockPilot не создаёт закупки автоматически и не принимает решения без пользователя." icon={<ShieldAlert className="h-5 w-5" />} />
      </section>
    </div>
  );
}

function RiskSummary({ title, value, tone }: { title: string; value: string; tone: "danger" | "warning" | "accent" }) {
  const tones = {
    danger: "bg-[color:var(--danger-soft)] text-[color:var(--danger)]",
    warning: "bg-[color:var(--warning-soft)] text-[color:var(--warning)]",
    accent: "bg-[color:var(--accent-soft)] text-[color:var(--accent)]",
  };
  return (
    <Surface className="p-5">
      <div className={cn("mb-4 inline-flex rounded-2xl p-2.5", tones[tone])}>
        <ShieldAlert className="h-5 w-5" />
      </div>
      <p className="text-sm text-[color:var(--muted)]">{title}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
    </Surface>
  );
}

function SeverityBadge({ level }: { level: string }) {
  const styles =
    level === "critical"
      ? "bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
      : level === "high"
        ? "bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
        : "bg-[color:var(--surface-muted)] text-[color:var(--muted-strong)]";
  const label = level === "critical" ? "критический" : level === "high" ? "высокий" : level === "medium" ? "средний" : "низкий";
  return <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium", styles)}>{label}</span>;
}

function RiskMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-3">
      <p className="text-xs text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function SignalCard({ title, body, icon }: { title: string; body: string; icon: React.ReactNode }) {
  return (
    <Surface className="p-5">
      <div className="mb-4 inline-flex rounded-2xl bg-[color:var(--surface-muted)] p-2.5 text-[color:var(--accent)]">{icon}</div>
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{body}</p>
    </Surface>
  );
}
