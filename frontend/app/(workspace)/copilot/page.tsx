"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, ClipboardList, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { getCopilotStatus, requestAnalysisAssist } from "@/src/lib/api/copilot";
import { API_URL } from "@/src/lib/constants";
import type { AnalysisAssistContext, ImportAssistResponse } from "@/src/types/api";

const QUICK_QUESTIONS = [
  "Что нужно сделать в первую очередь?",
  "Какие товары срочно докупить?",
  "Какие рекомендации требуют проверки?",
  "Где риск дефицита?",
  "Где возможен избыток запасов?",
  "Почему прогноз может быть ненадёжным?",
  "Сформируй краткое резюме для руководителя",
  "Какие SKU проверить вручную?",
] as const;

export default function CopilotPage() {
  const dashboard = useDashboardState();
  const hasAnalysis = Boolean(dashboard.result);
  const [question, setQuestion] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }
    return new URLSearchParams(window.location.search).get("q") ?? "";
  });
  const [answer, setAnswer] = useState<ImportAssistResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const statusQuery = useQuery({
    queryKey: ["copilot-status"],
    queryFn: getCopilotStatus,
    retry: 0,
  });

  const context = useMemo(() => {
    if (!dashboard.result) {
      return null;
    }
    return buildAnalysisAssistContext(dashboard);
  }, [dashboard]);

  async function askCopilot(nextQuestion: string) {
    if (!context) {
      setError("Сначала запустите анализ.");
      return;
    }

    const trimmedQuestion = nextQuestion.trim();
    if (!trimmedQuestion) {
      setError("Введите вопрос для Copilot.");
      return;
    }

    setIsLoading(true);
    setError("");
    setQuestion(trimmedQuestion);

    try {
      const response = await requestAnalysisAssist({
        question: trimmedQuestion,
        context,
      });
      setAnswer(response);
    } catch (requestError) {
      setAnswer(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "AI-помощник недоступен. Проверьте настройки YandexGPT и backend."
      );
    } finally {
      setIsLoading(false);
    }
  }

  if (!hasAnalysis) {
    return (
      <div className="space-y-6">
        <PageTitle title="Copilot" description="AI-помощник по текущему анализу." />
        <Surface className="p-6 md:p-7">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-md bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <Bot className="h-4 w-4" />
              Анализ ещё не запущен
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">Copilot появится после анализа</h2>
              <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                Загрузите файл продаж и остатков, чтобы AI-помощник мог объяснить рекомендации, риски и надёжность прогноза.
              </p>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <UiButton href="/overview#upload-panel" leadingIcon={<ClipboardList className="h-4 w-4" />}>
                Загрузить файл
              </UiButton>
              <a
                href={`${API_URL}/files/demo`}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
              >
                <Sparkles className="h-4 w-4" />
                Попробовать демо-файл
              </a>
            </div>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageTitle title="Copilot по анализу" description="Copilot отвечает только на основе текущего анализа." />

      <Surface className="overflow-hidden p-0">
        <div className="grid gap-0 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="border-b border-[color:var(--line)] p-6 lg:border-b-0 lg:border-r">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--accent-soft)] px-3 py-1.5 text-sm text-[color:var(--accent)]">
              <Bot className="h-4 w-4" />
              AI Copilot
            </div>
            <h2 className="mt-4 text-3xl font-semibold leading-tight">Спросите по текущему анализу</h2>
            <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">
              AI-пояснения формируются по агрегированному контексту анализа. Copilot не меняет закупочный план и не получает полный исходный файл.
            </p>
            {dashboard.isHistoryAnalysis && dashboard.activeAnalysisCreatedAt ? (
              <p className="mt-3 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-3 text-sm text-[color:var(--muted)]">
                Copilot отвечает по открытому анализу от {dashboard.activeAnalysisCreatedAt}.
              </p>
            ) : null}
          </div>
          <div>
            <div className="p-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">Статус AI:</span>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                    statusQuery.data?.available
                      ? "bg-[color:var(--success-soft)] text-[color:var(--success)]"
                      : "bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
                  }`}
                >
                  {statusQuery.data?.available ? "Подключён" : statusQuery.data?.configured ? "Проверка нужна" : "Не настроен"}
                </span>
              </div>
              <p className="mt-2 break-words text-sm text-[color:var(--muted)]">
                {statusQuery.data?.message ??
                  (statusQuery.isLoading
                    ? "Проверяем подключение к YandexGPT."
                    : "Не удалось получить статус Copilot. Проверьте backend и настройки YandexGPT.")}
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <ContextPill label="Файл" value={dashboard.activeAnalysisFilename ?? "текущий анализ"} />
                <ContextPill
                  label="Период"
                  value={
                    dashboard.datasetMeta?.startDate && dashboard.datasetMeta?.endDate
                      ? `${dashboard.datasetMeta.startDate} - ${dashboard.datasetMeta.endDate}`
                      : "нет данных"
                  }
                />
                <ContextPill label="SKU" value={dashboard.datasetMeta?.skuCount ? String(dashboard.datasetMeta.skuCount) : "нет данных"} />
              </div>
            </div>
          </div>
        </div>
      </Surface>

      <Surface className="p-5 md:p-6">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
          <Sparkles className="h-4 w-4 text-[color:var(--accent)]" />
          Быстрые вопросы
        </div>
        <div className="flex flex-wrap gap-2">
          {QUICK_QUESTIONS.map((item) => (
            <button
              key={item}
              onClick={() => void askCopilot(item)}
              className="rounded-full border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm transition hover:-translate-y-px hover:border-[color:var(--border-strong)]"
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </Surface>

      <Surface className="overflow-hidden p-0">
        <div className="border-b border-[color:var(--line)] bg-[color:var(--surface-2)] px-5 py-4">
          <h2 className="text-lg font-semibold">Ответ помощника</h2>
          <p className="mt-1 text-sm text-[color:var(--muted)]">Copilot не меняет данные и решения, а объясняет текущий анализ.</p>
        </div>
        <div className="p-5">
          <div className="flex flex-col gap-2 md:flex-row">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Спросите про риски, рекомендации или надёжность прогноза"
              className="h-11 flex-1 rounded-2xl border border-[color:var(--border)] bg-[color:var(--input-bg)] px-3 text-sm outline-none"
            />
            <UiButton onClick={() => void askCopilot(question)} loading={isLoading}>
              {isLoading ? "Думаем..." : "Спросить"}
            </UiButton>
          </div>

        {error ? (
          <div className="mt-4 rounded-lg border border-[color:var(--danger)] bg-[color:var(--danger-soft)] p-4 text-sm text-[color:var(--danger)]">
            {error}
          </div>
        ) : null}

        {answer ? (
          <div
            className={`mt-4 rounded-3xl border p-5 text-sm ${answer.fallback ? "border-[color:var(--warning)] bg-[color:var(--warning-soft)] text-[color:var(--warning)]" : "border-[color:var(--border)] bg-[color:var(--surface-muted)]"}`}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-[color:var(--muted)]">
              <span>{answer.provider}</span>
              <span>•</span>
              <span>{answer.model}</span>
              <span>•</span>
              <span>агрегированный контекст</span>
            </div>
            <div className="prose prose-sm max-w-none whitespace-normal text-[color:var(--text)] prose-p:leading-6 prose-strong:text-[color:var(--text)]">
              <ReactMarkdown>{answer.answer}</ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="mt-4 rounded-3xl border border-dashed border-[color:var(--line)] bg-[color:var(--surface-2)] p-6 text-sm leading-6 text-[color:var(--muted)]">
            Выберите быстрый вопрос или задайте свой. Ответ появится здесь и будет основан только на активном анализе.
          </div>
        )}
        </div>
      </Surface>
    </div>
  );
}

function ContextPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-3 py-2">
      <p className="text-[11px] uppercase text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 truncate text-sm font-medium">{value}</p>
    </div>
  );
}

function buildAnalysisAssistContext(dashboard: ReturnType<typeof useDashboardState>): AnalysisAssistContext {
  const result = dashboard.result;
  const reliability = dashboard.analysisReliability;
  const decisions = dashboard.purchaseRecommendations.slice(0, 12).map((item) => ({
    sku: item.sku,
    product_name: item.product_name,
    recommended_order_qty: item.recommended_order_qty,
    priority: item.priority,
    message: item.message,
  }));

  return {
    stage: "analysis",
    summary: {
      filename: dashboard.activeAnalysisFilename ?? null,
      period:
        dashboard.datasetMeta?.startDate && dashboard.datasetMeta?.endDate
          ? `${dashboard.datasetMeta.startDate} - ${dashboard.datasetMeta.endDate}`
          : null,
      sku_count: dashboard.datasetMeta?.skuCount ?? null,
      row_count: dashboard.datasetMeta?.totalRows ?? null,
    },
    kpis: {
      urgent_count: dashboard.summary.urgentCount,
      overstock_count: dashboard.summary.overstockCount,
      expected_revenue: dashboard.summary.totalExpectedRevenue,
      recommendation_count: result?.recommendations.length ?? 0,
    },
    top_recommendations: (dashboard.purchaseRecommendations ?? []).slice(0, 12).map((item) => ({
      sku: item.sku,
      product_name: item.product_name,
      category: item.category,
      recommended_order_qty: item.recommended_order_qty,
      stockout_risk: item.stockout_risk ?? null,
      priority: item.priority,
      reason: item.message,
    })),
    high_risk_items: (dashboard.stockoutCandidates ?? []).slice(0, 12).map((item) => ({
      sku: item.sku,
      product_name: item.product_name,
      stockout_risk: item.stockout_risk ?? null,
      current_stock: item.current_stock,
      stock_days_left: item.stock_days_left,
    })),
    overstock_items: (dashboard.overstockCandidates ?? []).slice(0, 12).map((item) => ({
      sku: item.sku,
      product_name: item.product_name,
      overstock_risk: item.overstock_risk ?? null,
      current_stock: item.current_stock,
      recommended_order_qty: item.recommended_order_qty,
    })),
    exceptions: (dashboard.anomalyFeed ?? []).slice(0, 12),
    forecast_quality: {
      overall_confidence: reliability?.forecast_quality.overall_confidence ?? null,
      reliability_score: reliability?.forecast_quality.reliability_score ?? null,
      wape: reliability?.forecast_quality.wape ?? null,
      mae: reliability?.forecast_quality.mae ?? null,
      bias: reliability?.forecast_quality.bias ?? null,
      backtest_period_days: reliability?.forecast_quality.backtest_period_days ?? null,
      coverage: reliability?.forecast_quality.coverage ?? null,
    },
    data_quality: {
      score: reliability?.data_quality.score ?? null,
      label: reliability?.data_quality.label ?? null,
      warnings_count: result?.data_quality?.warnings_count ?? 0,
      errors_count: result?.data_quality?.errors_count ?? 0,
    },
    reliability_warnings: [
      ...(reliability?.data_quality.warnings ?? []),
      ...(reliability?.forecast_quality.warnings ?? []),
      ...(reliability?.warnings ?? []),
    ].slice(0, 15),
    purchase_plan_decisions: decisions,
    selected_sku: dashboard.selectedSkuDetails
      ? {
          sku: dashboard.selectedSkuDetails.sku,
          product_name: dashboard.selectedSkuDetails.product_name,
          priority: dashboard.selectedSkuDetails.priority,
          recommended_order_qty: dashboard.selectedSkuDetails.recommended_order_qty,
          stockout_risk: dashboard.selectedSkuDetails.stockout_risk ?? null,
          confidence_score: dashboard.selectedSkuDetails.confidence_score ?? null,
        }
      : null,
  };
}
