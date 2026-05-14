"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { AlertTriangle, BarChart3, LineChart, ShieldCheck, Sparkles } from "lucide-react";
import { DemandTrendChart, ForecastConfidenceChart } from "@/src/components/app/charts";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { useI18n } from "@/src/i18n/provider";
import { formatCompactMoney, formatNumber, formatPercent } from "@/src/lib/format";
import { cn } from "@/src/lib/utils";

const copy = {
  ru: {
    notAvailable: "Нет данных",
    upload: "Загрузить файл",
    forecastRows: "SKU с прогнозом",
    predictedUnits: "Прогноз, ед.",
    expectedRevenue: "Ожидаемая выручка",
    confidence: "Надёжность",
    product: "Товар",
    category: "Категория",
    horizon: "Горизонт",
    demand: "Средний спрос",
    interval: "Диапазон",
    reason: "Причина",
    reliabilityPage: "Открыть надёжность анализа",
    activeOnly: "Страница показывает прогноз, диапазон и надёжность по текущему анализу.",
  },
  en: {
    notAvailable: "No data",
    upload: "Upload file",
    forecastRows: "Forecasted SKUs",
    predictedUnits: "Predicted units",
    expectedRevenue: "Expected revenue",
    confidence: "Надёжность",
    product: "Product",
    category: "Category",
    horizon: "Horizon",
    demand: "Average demand",
    interval: "Range",
    reason: "Reason",
    reliabilityPage: "Open analysis reliability",
    activeOnly: "Страница показывает прогноз, диапазон и надёжность по текущему анализу.",
  },
} as const;

export default function ForecastingPage() {
  const state = useDashboardState();
  const { t, locale } = useI18n();
  const text = copy[locale];
  const forecastItems = useMemo(() => state.result?.product_forecast ?? [], [state.result?.product_forecast]);
  const forecastQuality = state.analysisReliability?.forecast_quality ?? null;
  const reviewQueue = useMemo(
    () =>
      state.forecastGovernance
        .filter((item) => item.intervention_required)
        .slice(0, 10),
    [state.forecastGovernance]
  );
  const lowReliabilityCount = state.analysisReliability?.sku_reliability.filter(
    (item) => item.confidence === "low" || item.confidence === "insufficient_data"
  ).length ?? 0;

  const totalPredicted = forecastItems.reduce((sum, item) => sum + (item.predicted_quantity ?? 0), 0);
  const totalRevenue = forecastItems.reduce((sum, item) => sum + (item.expected_revenue ?? 0), 0);

  if (!state.result) {
    return (
      <div className="space-y-6">
        <PageTitle title={t("page.forecasting.title")} description={t("page.forecasting.desc")} />
        <Surface className="p-6 md:p-8">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <LineChart className="h-4 w-4" />
              {t("forecast.insufficient")}
            </div>
            <h2 className="text-2xl font-semibold">{t("forecast.empty.title")}</h2>
            <p className="text-sm leading-6 text-[color:var(--muted)]">{t("forecast.empty.desc")}</p>
            <UiButton href="/overview#upload-panel">{text.upload}</UiButton>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageTitle title={t("page.forecasting.title")} description={t("page.forecasting.desc")} />

      <Surface className="overflow-hidden p-0">
        <div className="grid gap-0 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="p-6 md:p-7">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[color:var(--accent-soft)] px-3 py-1.5 text-sm text-[color:var(--accent)]">
              <Sparkles className="h-4 w-4" />
              {t("page.forecasting.lab")}
            </div>
            <h2 className="text-3xl font-semibold leading-tight">{t("forecast.summary.title")}</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-[color:var(--muted)]">{text.activeOnly}</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <SummaryCard title={text.forecastRows} value={formatNumber(forecastItems.length, 0)} icon={<BarChart3 className="h-5 w-5" />} />
              <SummaryCard title={text.predictedUnits} value={formatNumber(totalPredicted, 0)} icon={<LineChart className="h-5 w-5" />} />
              <SummaryCard title={text.expectedRevenue} value={formatCompactMoney(totalRevenue)} icon={<Sparkles className="h-5 w-5" />} />
              <SummaryCard title={t("forecast.sku_to_review")} value={formatNumber(lowReliabilityCount, 0)} icon={<AlertTriangle className="h-5 w-5" />} />
            </div>
          </div>
          <div className="border-t border-[color:var(--line)] bg-[color:var(--surface-2)] p-6 md:p-7 lg:border-l lg:border-t-0">
            <div className="grid gap-3 sm:grid-cols-2">
              <QualityCard
                title={t("forecast.reliability")}
                value={translateConfidence(forecastQuality?.overall_confidence, locale)}
                tone={forecastQuality?.overall_confidence ?? "insufficient_data"}
              />
              <QualityCard title={t("forecast.wape")} value={formatRate(forecastQuality?.wape)} />
              <QualityCard title={t("forecast.mae")} value={formatNumber(forecastQuality?.mae, 1)} />
              <QualityCard title={t("forecast.bias")} value={formatRate(forecastQuality?.bias)} />
            </div>
            <UiButton href="/reliability" variant="secondary" className="mt-5">
              {t("forecast.open_reliability")}
            </UiButton>
          </div>
        </div>
      </Surface>

      <Surface className="p-5 md:p-6">
        <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Динамика спроса и прогноз</h2>
            <p className="mt-1 text-sm text-[color:var(--muted)]">Исторические продажи и прогноз по текущему анализу.</p>
          </div>
        </div>
        <DemandTrendChart />
      </Surface>

      <Surface className="p-5 md:p-6">
        <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">{t("forecast.chart_title")}</h2>
            <p className="mt-1 text-sm text-[color:var(--muted)]">{t("chart.confidence_hint")}</p>
          </div>
        </div>
        <ForecastConfidenceChart />
      </Surface>

      <section className="grid gap-4 xl:grid-cols-[0.78fr_1.22fr]">
        <Surface className="p-5 md:p-6">
          <h2 className="text-lg font-semibold">{t("forecast.governance")}</h2>
          <div className="mt-4 space-y-3">
            {reviewQueue.length > 0 ? (
              reviewQueue.map((item) => (
                <div key={item.sku} className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold">{item.sku}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-[color:var(--muted)]">{item.product_name}</p>
                    </div>
                    <ConfidenceBadge value={item.confidence_score} />
                  </div>
                  <p className="mt-3 text-xs text-[color:var(--muted)]">
                    {item.intervention_required ? t("forecast.review_required") : t("forecast.on_track")}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4 text-sm text-[color:var(--muted)]">
                {t("forecast.on_track")}
              </div>
            )}
          </div>
        </Surface>

        <Surface className="overflow-hidden p-0">
          <div className="border-b border-[color:var(--line)] px-5 py-4">
            <h2 className="text-lg font-semibold">{t("forecast.table_title")}</h2>
          </div>
          <div className="max-h-[36rem] overflow-auto">
            <table className="min-w-[980px] w-full text-sm">
              <thead className="sticky top-0 z-10 bg-[color:var(--table-header)] text-left text-[color:var(--muted)] shadow-[inset_0_-1px_0_var(--line)]">
                <tr>
                  <th className="px-5 py-3 font-medium">SKU</th>
                  <th className="px-5 py-3 font-medium">{text.product}</th>
                  <th className="px-5 py-3 font-medium">{text.category}</th>
                  <th className="px-5 py-3 font-medium">{text.horizon}</th>
                  <th className="px-5 py-3 font-medium">{text.demand}</th>
                  <th className="px-5 py-3 font-medium">{text.predictedUnits}</th>
                  <th className="px-5 py-3 font-medium">{text.interval}</th>
                  <th className="px-5 py-3 font-medium">{text.confidence}</th>
                </tr>
              </thead>
              <tbody>
                {forecastItems.slice(0, 100).map((item) => (
                  <tr key={item.sku} className="border-t border-[color:var(--line)] align-top hover:bg-[color:var(--table-row-hover)]">
                    <td className="px-5 py-3 font-medium">{item.sku}</td>
                    <td className="px-5 py-3">
                      <div className="max-w-[22rem] break-words">{item.product_name}</div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">{item.forecast_model ?? text.notAvailable}</div>
                    </td>
                    <td className="px-5 py-3">{item.category || text.notAvailable}</td>
                    <td className="px-5 py-3">{formatNumber(item.horizon_days, 0)}</td>
                    <td className="px-5 py-3">{formatNumber(item.average_daily_demand, 1)}</td>
                    <td className="px-5 py-3 font-semibold">{formatNumber(item.predicted_quantity, 0)}</td>
                    <td className="px-5 py-3">
                      {formatNumber(item.lower_bound, 0)} - {formatNumber(item.upper_bound, 0)}
                    </td>
                    <td className="px-5 py-3">
                      <ConfidenceBadge value={item.confidence_score} label={item.confidence_label} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
      </section>
    </div>
  );
}

function SummaryCard({ title, value, icon }: { title: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
      <div className="mb-3 inline-flex rounded-2xl bg-[color:var(--surface-3)] p-2 text-[color:var(--accent)]">{icon}</div>
      <p className="text-sm text-[color:var(--muted)]">{title}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function QualityCard({
  title,
  value,
  tone,
}: {
  title: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface)] p-4">
      <div className="mb-2 flex items-center gap-2">
        <ShieldCheck className={cn("h-4 w-4", confidenceColor(tone))} />
        <p className="text-sm text-[color:var(--muted)]">{title}</p>
      </div>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}

function ConfidenceBadge({ value, label }: { value?: number | null; label?: string | null }) {
  const tone = typeof value === "number" ? (value >= 75 ? "high" : value >= 55 ? "medium" : "low") : label;
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2.5 py-1 text-xs font-medium",
        tone === "high"
          ? "border-[color:var(--success)] bg-[color:var(--success-soft)] text-[color:var(--success)]"
          : tone === "medium"
            ? "border-[color:var(--warning)] bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
            : "border-[color:var(--danger)] bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
      )}
    >
      {typeof value === "number" ? `${formatNumber(value, 0)}%` : label ?? "—"}
    </span>
  );
}

function translateConfidence(value: string | undefined | null, locale: "ru" | "en") {
  const ru: Record<string, string> = {
    high: "Высокая",
    medium: "Средняя",
    low: "Низкая",
    insufficient_data: "Недостаточно данных",
  };
  const en: Record<string, string> = {
    high: "High",
    medium: "Medium",
    low: "Low",
    insufficient_data: "Insufficient data",
  };
  if (!value) {
    return locale === "ru" ? ru.insufficient_data : en.insufficient_data;
  }
  return (locale === "ru" ? ru : en)[value] ?? value;
}

function confidenceColor(value: string | undefined | null) {
  if (value === "high") {
    return "text-[color:var(--success)]";
  }
  if (value === "medium") {
    return "text-[color:var(--warning)]";
  }
  return "text-[color:var(--danger)]";
}

function formatRate(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }
  return formatPercent(value * 100, 1);
}
