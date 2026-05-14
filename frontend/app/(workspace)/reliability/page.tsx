"use client";

import { Info, ShieldCheck } from "lucide-react";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { formatNumber } from "@/src/lib/format";
import { cn } from "@/src/lib/utils";

export default function ReliabilityPage() {
  const state = useDashboardState();
  const reliability = state.analysisReliability;

  if (!state.result || !reliability) {
    return (
      <div className="space-y-6">
        <PageTitle
          title="Надёжность анализа"
          description="Качество данных, надёжность прогноза и ограничения анализа по SKU."
        />
        <Surface className="p-6 md:p-7">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-md bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <ShieldCheck className="h-4 w-4" />
              Нет данных по надёжности
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">Надёжность анализа появится после загрузки файла</h2>
              <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                StockPilot проверит качество данных, оценит прогноз и покажет, каким рекомендациям можно доверять больше.
              </p>
            </div>
            <UiButton href="/overview#upload-panel">Загрузить файл</UiButton>
          </div>
        </Surface>
      </div>
    );
  }

  const lowConfidenceCount = reliability.sku_reliability.filter((item) => item.confidence === "low").length;
  const warnings = [
    ...reliability.data_quality.warnings,
    ...reliability.forecast_quality.warnings,
    ...reliability.warnings,
  ];

  return (
    <div className="space-y-7">
      <PageTitle
        title="Надёжность анализа"
        description="Честная оценка качества данных и ограничений прогноза без обещаний магической точности."
      />

      <div className="flex flex-wrap gap-2">
        <UiButton
          href="/copilot?q=Почему%20прогноз%20может%20быть%20ненадёжным%3F"
          variant="secondary"
        >
          Объяснить надёжность прогноза
        </UiButton>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <SummaryCard title="Качество данных" value={reliability.data_quality.score != null ? `${reliability.data_quality.score}/100` : "Нет данных"} />
        <SummaryCard title="Надёжность прогноза" value={confidenceLabel(reliability.forecast_quality.overall_confidence)} />
        <SummaryCard title="WAPE" value={reliability.forecast_quality.wape != null ? formatMetricPercent(reliability.forecast_quality.wape) : "Недостаточно данных"} />
        <SummaryCard title="Bias" value={reliability.forecast_quality.bias != null ? formatMetricPercent(reliability.forecast_quality.bias) : "Недостаточно данных"} />
        <SummaryCard title="SKU с низкой надёжностью" value={formatNumber(lowConfidenceCount, 0)} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Surface className="p-6">
          <h2 className="text-base font-semibold">Что влияет на надёжность</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <InfluenceCard title="Короткая история" description="Если данных мало, честный backtest невозможен или слишком нестабилен." />
            <InfluenceCard title="Нестабильный спрос" description="Сильные колебания спроса делают прогноз менее устойчивым." />
            <InfluenceCard title="Нулевые остатки" description="Нули в продажах при нулевом остатке могут искажать оценку реального спроса." />
            <InfluenceCard title="Промо-периоды" description="Акции могут временно разгонять спрос и ухудшать интерпретацию прогноза." />
            <InfluenceCard title="Пропуски и ошибки" description="Проблемы в данных напрямую влияют на качество рекомендаций и доверие к ним." />
          </div>
        </Surface>

        <Surface className="p-6">
          <h2 className="text-base font-semibold">Как читать метрики</h2>
          <div className="mt-4 space-y-3">
            <ExplainCard
              title="WAPE"
              description="Средняя относительная ошибка прогноза с учётом объёма продаж. Чем ниже, тем лучше."
            />
            <ExplainCard
              title="Bias"
              description="Показывает, завышает или занижает модель спрос. Положительный bias — завышение, отрицательный — занижение."
            />
            <ExplainCard
              title="Надёжность"
              description="Общий уровень доверия к прогнозу. Он зависит от качества истории, стабильности спроса и результатов backtest."
            />
            <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4 text-sm text-[color:var(--muted)]">
              Backtest период: {reliability.forecast_quality.backtest_period_days ?? "Нет данных"} дней • Coverage:{" "}
              {reliability.forecast_quality.coverage != null
                ? formatMetricPercent(reliability.forecast_quality.coverage)
                : "Недостаточно данных"}
            </div>
          </div>
        </Surface>
      </section>

      <Surface className="p-6">
        <h2 className="text-base font-semibold">Предупреждения</h2>
        {warnings.length > 0 ? (
          <div className="mt-4 space-y-3">
            {warnings.map((warning, index) => (
              <div key={`${warning.code}-${index}`} className="rounded-lg border border-[color:var(--warning)] bg-[color:var(--warning-soft)] p-4">
                <p className="text-sm font-semibold text-[color:var(--warning)]">{warning.title}</p>
                <p className="mt-1 text-sm text-[color:var(--warning)]">{warning.message}</p>
                {warning.suggestion ? <p className="mt-2 text-sm text-[color:var(--warning)]">{warning.suggestion}</p> : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4 text-sm text-[color:var(--muted)]">
            Критичных предупреждений по надёжности не найдено.
          </div>
        )}
      </Surface>

      <Surface className="overflow-hidden p-0">
        <div className="border-b border-[color:var(--border)] p-6">
          <h2 className="text-base font-semibold">Надёжность по SKU</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-[1100px] w-full text-sm">
            <thead className="bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">SKU</th>
                <th className="px-4 py-3 font-medium">Товар</th>
                <th className="px-4 py-3 font-medium">Категория</th>
                <th className="px-4 py-3 font-medium">Надёжность</th>
                <th className="px-4 py-3 font-medium">WAPE</th>
                <th className="px-4 py-3 font-medium">MAE</th>
                <th className="px-4 py-3 font-medium">Bias</th>
                <th className="px-4 py-3 font-medium">Причина</th>
                <th className="px-4 py-3 font-medium">Рекомендация</th>
              </tr>
            </thead>
            <tbody>
              {reliability.sku_reliability.map((item) => (
                <tr key={item.sku} className="border-t border-[color:var(--border)] align-top">
                  <td className="px-4 py-3 font-medium">{item.sku}</td>
                  <td className="px-4 py-3">{item.product_name}</td>
                  <td className="px-4 py-3">{item.category}</td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge confidence={item.confidence} />
                  </td>
                  <td className="px-4 py-3">{item.wape != null ? formatMetricPercent(item.wape) : "Недостаточно данных"}</td>
                  <td className="px-4 py-3">{item.mae != null ? formatNumber(item.mae, 2) : "Недостаточно данных"}</td>
                  <td className="px-4 py-3">{item.bias != null ? formatMetricPercent(item.bias) : "Недостаточно данных"}</td>
                  <td className="px-4 py-3">{item.reason}</td>
                  <td className="px-4 py-3 text-[color:var(--muted)]">{userRecommendation(item.confidence)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Surface>
    </div>
  );
}

function SummaryCard({ title, value }: { title: string; value: string }) {
  return (
    <Surface className="p-5">
      <p className="text-xs font-medium uppercase text-[color:var(--muted)]">{title}</p>
      <p className="mt-2 text-xl font-semibold leading-7">{value}</p>
    </Surface>
  );
}

function InfluenceCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm text-[color:var(--muted)]">{description}</p>
    </div>
  );
}

function ExplainCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
      <div className="flex items-start gap-2">
        <Info className="mt-0.5 h-4 w-4 text-[color:var(--muted)]" />
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="mt-1 text-sm text-[color:var(--muted)]">{description}</p>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const styles = {
    high: "bg-[color:var(--success-soft)] text-[color:var(--success)]",
    medium: "bg-[color:var(--warning-soft)] text-[color:var(--warning)]",
    low: "bg-[color:var(--danger-soft)] text-[color:var(--danger)]",
    insufficient_data: "bg-[color:var(--surface-muted)] text-[color:var(--muted-strong)]",
  };

  return (
    <span className={cn("inline-flex items-center rounded-md px-2 py-1 text-xs font-medium", styles[confidence as keyof typeof styles] ?? styles.insufficient_data)}>
      {confidenceLabel(confidence)}
    </span>
  );
}

function confidenceLabel(value: string) {
  switch (value) {
    case "high":
      return "Высокая";
    case "medium":
      return "Средняя";
    case "low":
      return "Низкая";
    case "insufficient_data":
      return "Недостаточно данных";
    default:
      return value;
  }
}

function formatMetricPercent(value: number) {
  return `${formatNumber(value * 100, 1)}%`;
}

function userRecommendation(confidence: string) {
  switch (confidence) {
    case "high":
      return "Можно использовать как рабочий ориентир.";
    case "medium":
      return "Проверьте вместе с остатками и историей продаж.";
    case "low":
      return "Проверьте перед закупкой.";
    default:
      return "Соберите больше истории перед интерпретацией.";
  }
}
