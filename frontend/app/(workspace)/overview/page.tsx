"use client";

import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  ClipboardList,
  Download,
  FileWarning,
  Package,
  ShieldAlert,
  Sparkles,
  ShieldCheck,
  TrendingDown,
} from "lucide-react";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { UploadPanel } from "@/src/components/app/upload-panel";
import { formatCompactMoney, formatDateTime, formatNumber } from "@/src/lib/format";
import { API_URL } from "@/src/lib/constants";
import { cn } from "@/src/lib/utils";

export default function OverviewPage() {
  const state = useDashboardState();
  const latestRun = state.history[0] ?? null;
  const hasAnalysis = Boolean(state.result);
  const activeFilename = state.activeAnalysisFilename ?? latestRun?.original_filename ?? null;
  const demoMode = /demo|sample/i.test(activeFilename ?? "");

  const stockoutCount = state.stockoutCandidates.length;
  const overstockCount = state.overstockCandidates.length;
  const urgentPurchaseCount = state.purchaseRecommendations.filter((item) => item.priority === "critical" || item.priority === "high").length;
  const anomalyCount = state.anomalyFeed.length;
  const qualityIssuesCount =
    (state.result?.data_quality?.warnings_count ?? 0) + (state.result?.data_quality?.errors_count ?? 0);

  const datasetMeta = state.datasetMeta;
  const reportHref = state.result?.report_url ? withApiBase(state.result.report_url) : null;
  const reportsHref = hasAnalysis ? "/reports" : "#upload-panel";
  const reliabilitySummary = state.reliabilitySummary;
  const executiveSummary = buildExecutiveSummary({
    hasAnalysis,
    urgentPurchaseCount,
    stockoutCount,
    overstockCount,
    qualityIssuesCount,
    anomalyCount,
  });
  const nextSteps = buildNextSteps({
    urgentPurchaseCount,
    stockoutCount,
    overstockCount,
    qualityIssuesCount,
    anomalyCount,
    hasAnalysis,
  });

  return (
    <div className="space-y-7">
      <PageTitle
        title={hasAnalysis ? "Главная" : "Начните с загрузки файла продаж и остатков"}
        description={
          hasAnalysis
            ? "Рабочая сводка по продажам, запасам и рекомендациям на сегодня."
            : "StockPilot проверит структуру файла, поможет сопоставить колонки, построит анализ и сформирует закупочные рекомендации."
        }
      />

      {hasAnalysis ? (
        <>
          <section className="grid gap-4 xl:grid-cols-[1.7fr_1fr]">
            <Surface className="p-6 md:p-7">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge tone="neutral">
                      {demoMode ? "Демо-данные" : "Локальный анализ"}
                    </StatusBadge>
                    {state.activeAnalysisCreatedAt ? (
                      <StatusBadge tone="neutral">
                        {state.isHistoryAnalysis ? "Открыт из истории" : "Последний запуск"}: {formatDateTime(state.activeAnalysisCreatedAt)}
                      </StatusBadge>
                    ) : null}
                    {activeFilename ? <StatusBadge tone="neutral">Файл: {activeFilename}</StatusBadge> : null}
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-2xl font-semibold leading-tight md:text-[2rem]">
                      {executiveSummary.title}
                    </h2>
                    <p className="max-w-3xl text-sm leading-6 text-[color:var(--muted)]">
                      {executiveSummary.description}
                    </p>
                  </div>
                </div>

                <div className="grid min-w-[220px] gap-2 sm:grid-cols-2 xl:grid-cols-1">
                  <QuickMeta
                    label="Период данных"
                    value={
                      datasetMeta?.startDate && datasetMeta?.endDate
                        ? `${datasetMeta.startDate} - ${datasetMeta.endDate}`
                        : "Нет данных"
                    }
                  />
                  <QuickMeta
                    label="SKU"
                    value={datasetMeta?.skuCount ? formatNumber(datasetMeta.skuCount, 0) : "Нет данных"}
                  />
                  <QuickMeta
                    label="Строк"
                    value={datasetMeta?.totalRows ? formatNumber(datasetMeta.totalRows, 0) : "Нет данных"}
                  />
                  <QuickMeta
                    label="Выручка по рекомендациям"
                    value={formatCompactMoney(state.summary.totalExpectedRevenue)}
                  />
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-2.5">
                <UiButton href="/planning" leadingIcon={<ClipboardList className="h-4 w-4" />}>
                  Открыть закупочный план
                </UiButton>
                <UiButton href="/exceptions" variant="secondary" leadingIcon={<ShieldAlert className="h-4 w-4" />}>
                  Посмотреть риски
                </UiButton>
                {reportHref ? (
                  <a
                    href={reportHref}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
                  >
                    <Download className="h-4 w-4" />
                    Скачать Excel-отчёт
                  </a>
                ) : (
                  <UiButton href={reportsHref} variant="secondary" leadingIcon={<ArrowRight className="h-4 w-4" />}>
                    Открыть отчёты
                  </UiButton>
                )}
                <UiButton href="/copilot" variant="ghost" leadingIcon={<Bot className="h-4 w-4" />}>
                  Открыть Copilot
                </UiButton>
                <UiButton
                  href="/copilot?q=Что%20нужно%20сделать%20в%20первую%20очередь%3F"
                  variant="ghost"
                  leadingIcon={<Bot className="h-4 w-4" />}
                >
                  Спросить Copilot по анализу
                </UiButton>
              </div>
            </Surface>

            <Surface className="p-6">
              <h2 className="text-base font-semibold">Что делать дальше</h2>
              <ul className="mt-4 space-y-3">
                {nextSteps.map((step) => (
                  <li key={step.title} className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3">
                    <p className="text-sm font-medium">{step.title}</p>
                    <p className="mt-1 text-sm text-[color:var(--muted)]">{step.description}</p>
                  </li>
                ))}
              </ul>
              <div className="mt-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-3 text-sm text-[color:var(--muted)]">
                Copilot по файлу доступен на этапе загрузки. Для текущего анализа можно открыть существующую страницу Copilot.
              </div>
            </Surface>
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <ActionCard
              title="Срочно докупить"
              value={formatNumber(urgentPurchaseCount, 0)}
              subtitle={urgentPurchaseCount > 0 ? "товаров с приоритетной закупкой" : "срочных закупок не найдено"}
              tone="critical"
              href="/planning"
              icon={<Package className="h-5 w-5" />}
            />
            <ActionCard
              title="Риск дефицита"
              value={formatNumber(stockoutCount, 0)}
              subtitle={stockoutCount > 0 ? "SKU с повышенным риском" : "критичных SKU не найдено"}
              tone="warning"
              href="/exceptions"
              icon={<ShieldAlert className="h-5 w-5" />}
            />
            <ActionCard
              title="Избыток запасов"
              value={formatNumber(overstockCount, 0)}
              subtitle={overstockCount > 0 ? "SKU с риском избытка" : "избыточных остатков не найдено"}
              tone="neutral"
              href="/planning"
              icon={<TrendingDown className="h-5 w-5" />}
            />
            <ActionCard
              title="Аномалии и исключения"
              value={formatNumber(anomalyCount, 0)}
              subtitle={anomalyCount > 0 ? "сигналов требуют проверки" : "аномалий не найдено"}
              tone="warning"
              href="/exceptions"
              icon={<AlertTriangle className="h-5 w-5" />}
            />
            <ActionCard
              title="Качество данных"
              value={formatNumber(qualityIssuesCount, 0)}
              subtitle={qualityIssuesCount > 0 ? "предупреждений и ошибок" : "критичных проблем не найдено"}
              tone={qualityIssuesCount > 0 ? "warning" : "success"}
              href="/reports"
              icon={<FileWarning className="h-5 w-5" />}
            />
          </section>

          {reliabilitySummary ? (
            <Surface className="p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="space-y-1">
                  <div className="inline-flex items-center gap-2 text-sm font-medium">
                    <ShieldCheck className="h-4 w-4 text-[color:var(--muted)]" />
                    Надёжность анализа
                  </div>
                  <p className="text-sm text-[color:var(--muted)]">
                    Надёжность прогноза: {translateConfidence(reliabilitySummary.overallConfidence)} • Качество данных:{" "}
                    {reliabilitySummary.dataQualityScore != null ? `${reliabilitySummary.dataQualityScore}/100` : "Нет данных"} • Есть{" "}
                    {formatNumber(reliabilitySummary.warningCount, 0)} предупреждений
                  </p>
                </div>
                <UiButton href="/reliability" variant="secondary" leadingIcon={<ArrowRight className="h-4 w-4" />}>
                  Подробнее о надёжности
                </UiButton>
              </div>
            </Surface>
          ) : null}

          <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <Surface className="p-6">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold">Что требует внимания</h2>
                  <p className="mt-1 text-sm text-[color:var(--muted)]">
                    Список приоритетов на основе текущего анализа без лишних графиков на первом экране.
                  </p>
                </div>
                <Link href="/planning" className="text-sm font-medium text-[color:var(--accent)]">
                  Открыть план
                </Link>
              </div>
              <div className="mt-4 space-y-3">
                <AttentionItem
                  title="Высокий риск дефицита"
                  description={
                    stockoutCount > 0
                      ? `${formatNumber(stockoutCount, 0)} товаров могут закончиться раньше следующей поставки.`
                      : "По текущему анализу критичных позиций не найдено."
                  }
                  tone="critical"
                />
                <AttentionItem
                  title="Избыточные остатки"
                  description={
                    overstockCount > 0
                      ? `${formatNumber(overstockCount, 0)} товаров имеют риск избытка запасов.`
                      : "Явных сигналов по избытку запасов не найдено."
                  }
                  tone="neutral"
                />
                <AttentionItem
                  title="Качество данных"
                  description={
                    qualityIssuesCount > 0
                      ? `Есть ${formatNumber(qualityIssuesCount, 0)} предупреждений по качеству данных. Проверьте отчёт и структуру файла.`
                      : "Критичных замечаний по качеству данных не найдено."
                  }
                  tone={qualityIssuesCount > 0 ? "warning" : "success"}
                />
                <AttentionItem
                  title="Проверка прогноза"
                  description={
                    state.summary.medianConfidence > 0
                      ? `Медианная надёжность прогноза: ${formatNumber(state.summary.medianConfidence, 0)}. Используйте эту оценку как ориентир, а не как гарантированный результат.`
                      : "Недостаточно данных, чтобы показать ориентир по прогнозу."
                  }
                  tone="neutral"
                />
              </div>
            </Surface>

            <Surface className="p-6">
              <h2 className="text-base font-semibold">Куда перейти дальше</h2>
              <div className="mt-4 grid gap-3">
                <RouteCard
                  href="/planning"
                  title="Закупочный план"
                  description="Список SKU с рекомендациями по заказу и приоритетами."
                />
                <RouteCard
                  href="/exceptions"
                  title="Риски"
                  description="Проверьте позиции с риском дефицита, аномалиями и слабым покрытием."
                />
                <RouteCard
                  href="/reports"
                  title="Отчёты"
                  description="Откройте локальные артефакты анализа и скачайте Excel или CSV."
                />
                <RouteCard
                  href="/history"
                  title="История"
                  description="Сравните последние локальные запуски и используемые параметры."
                />
              </div>
            </Surface>
          </section>
        </>
      ) : (
        <section className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
          <Surface className="p-6 md:p-7">
            <div className="space-y-4">
              <StatusBadge tone="neutral">Без анализа</StatusBadge>
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold leading-tight md:text-[2rem]">
                  Загрузите файл и получите рабочую сводку по запасам и продажам
                </h2>
                <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                  StockPilot проверит структуру файла, поможет сопоставить колонки, построит анализ и сформирует закупочные рекомендации.
                </p>
              </div>
              <div className="flex flex-wrap gap-2.5">
                <a
                  href="#upload-panel"
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-4 text-sm font-medium text-white shadow-[var(--shadow-sm)] transition-all duration-200 hover:-translate-y-px"
                >
                  <Package className="h-4 w-4" />
                  Загрузить файл
                </a>
                <a
                  href={`${API_URL}/files/demo`}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
                >
                  <Sparkles className="h-4 w-4" />
                  Попробовать демо-файл
                </a>
                <a
                  href={`${API_URL}/files/template`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
                >
                  <Download className="h-4 w-4" />
                  Скачать шаблон
                </a>
              </div>
            </div>
          </Surface>

          <Surface className="p-6">
            <h2 className="text-base font-semibold">Что будет после загрузки</h2>
            <div className="mt-4 space-y-3">
              <EmptyStep title="Проверка структуры" description="StockPilot покажет колонки, период данных и пример строк до анализа." />
              <EmptyStep title="Сопоставление колонок" description="Если названия отличаются от шаблона, мастер импорта предложит варианты и даст подтвердить их вручную." />
              <EmptyStep title="Нормализация и анализ" description="После проверки файл будет подготовлен к анализу без изменения исходной логики расчётов." />
              <EmptyStep title="Рекомендации и отчёты" description="Вы увидите риски, закупочные действия и сможете открыть локальные артефакты анализа." />
            </div>
          </Surface>
        </section>
      )}

      <div id="upload-panel">
        <UploadPanel />
      </div>
    </div>
  );
}

function ActionCard({
  title,
  value,
  subtitle,
  tone,
  href,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  tone: "critical" | "warning" | "success" | "neutral";
  href: string;
  icon: React.ReactNode;
}) {
  const toneClass = {
    critical: "text-[color:var(--danger)] bg-[color:var(--danger-soft)] border-[color:var(--danger)]",
    warning: "text-[color:var(--warning)] bg-[color:var(--warning-soft)] border-[color:var(--warning)]",
    success: "text-[color:var(--success)] bg-[color:var(--success-soft)] border-[color:var(--success)]",
    neutral: "text-[color:var(--text)] bg-[color:var(--surface-muted)] border-[color:var(--border)]",
  };

  return (
    <Link href={href}>
      <Surface className="h-full p-5 transition-all duration-200 hover:-translate-y-px hover:border-[color:var(--border-strong)]">
        <div className="flex items-start justify-between gap-3">
          <div className={cn("rounded-lg border p-2.5", toneClass[tone])}>{icon}</div>
          <ArrowRight className="h-4 w-4 text-[color:var(--muted)]" />
        </div>
        <p className="mt-4 text-sm font-medium text-[color:var(--muted)]">{title}</p>
        <p className="mt-1 text-3xl font-semibold">{value}</p>
        <p className="mt-2 text-sm text-[color:var(--muted)]">{subtitle}</p>
      </Surface>
    </Link>
  );
}

function AttentionItem({
  title,
  description,
  tone,
}: {
  title: string;
  description: string;
  tone: "critical" | "warning" | "success" | "neutral";
}) {
  const toneClass = {
    critical: "border-[color:var(--danger)] bg-[color:var(--danger-soft)]",
    warning: "border-[color:var(--warning)] bg-[color:var(--warning-soft)]",
    success: "border-[color:var(--success)] bg-[color:var(--success-soft)]",
    neutral: "border-[color:var(--border)] bg-[color:var(--surface-muted)]",
  };

  return (
    <div className={cn("rounded-lg border p-3.5", toneClass[tone])}>
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm text-[color:var(--muted)]">{description}</p>
    </div>
  );
}

function RouteCard({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3.5 transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface)]"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="mt-1 text-sm text-[color:var(--muted)]">{description}</p>
        </div>
        <ArrowRight className="h-4 w-4 shrink-0 text-[color:var(--muted)]" />
      </div>
    </Link>
  );
}

function QuickMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-3 py-2.5">
      <p className="text-xs font-medium uppercase text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}

function StatusBadge({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone: "neutral" | "success";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium",
        tone === "success"
          ? "bg-[color:var(--success-soft)] text-[color:var(--success)]"
          : "bg-[color:var(--surface-muted)] text-[color:var(--muted)]"
      )}
    >
      {tone === "success" ? <CheckCircle2 className="h-3.5 w-3.5" /> : null}
      {children}
    </span>
  );
}

function EmptyStep({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3.5">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm text-[color:var(--muted)]">{description}</p>
    </div>
  );
}

function buildExecutiveSummary(params: {
  hasAnalysis: boolean;
  urgentPurchaseCount: number;
  stockoutCount: number;
  overstockCount: number;
  qualityIssuesCount: number;
  anomalyCount: number;
}) {
  if (!params.hasAnalysis) {
    return {
      title: "Анализ ещё не запущен",
      description: "Загрузите файл, чтобы получить рабочую сводку по продажам, остаткам и закупочным действиям.",
    };
  }

  if (params.urgentPurchaseCount > 0 || params.stockoutCount > 0) {
    return {
      title: `Сегодня в фокусе дефицит и приоритетные закупки`,
      description:
        `StockPilot нашёл ${formatNumber(Math.max(params.urgentPurchaseCount, params.stockoutCount), 0)} позиций, ` +
        "которые требуют внимания в первую очередь. Проверьте закупочный план и риски дефицита перед следующей поставкой.",
    };
  }

  if (params.overstockCount > 0) {
    return {
      title: "Основной риск сейчас связан с избыточными остатками",
      description:
        "Критичных дефицитов не найдено, но часть SKU может держать лишний запас. Проверьте позиции с низкой оборачиваемостью и рекомендации по заказу.",
    };
  }

  if (params.qualityIssuesCount > 0 || params.anomalyCount > 0) {
    return {
      title: "Анализ построен, но есть сигналы для дополнительной проверки",
      description:
        "Перед тем как делиться выводами с командой, проверьте предупреждения по качеству данных и аномалии в спросе.",
    };
  }

  return {
    title: "Анализ готов: критичных сигналов немного, можно переходить к плану закупок",
    description:
      "Структура данных принята, основные риски умеренные. Откройте закупочный план и отчёты, чтобы зафиксировать действия по SKU.",
  };
}

function buildNextSteps(params: {
  urgentPurchaseCount: number;
  stockoutCount: number;
  overstockCount: number;
  qualityIssuesCount: number;
  anomalyCount: number;
  hasAnalysis: boolean;
}) {
  if (!params.hasAnalysis) {
    return [
      { title: "Загрузите CSV или XLSX", description: "Начните с файла продаж и остатков, чтобы открыть предварительную проверку и мастер импорта." },
      { title: "Проверьте структуру файла", description: "StockPilot покажет обязательные колонки и предупредит о проблемах до анализа." },
      { title: "Запустите анализ", description: "После нормализации будет доступен расчёт рекомендаций и локальные артефакты." },
    ];
  }

  return [
    {
      title: "Проверьте товары с высоким риском дефицита",
      description:
        params.stockoutCount > 0
          ? `Сейчас в зоне риска ${formatNumber(params.stockoutCount, 0)} SKU.`
          : "Сейчас нет выраженных сигналов по дефициту.",
    },
    {
      title: "Откройте закупочный план",
      description:
        params.urgentPurchaseCount > 0
          ? `Приоритетная закупка нужна для ${formatNumber(params.urgentPurchaseCount, 0)} товаров.`
          : "План можно использовать для контрольной проверки запасов и заказа.",
    },
    {
      title: "Скачайте отчёт для команды",
      description: "Откройте локальные артефакты анализа и выгрузите Excel или CSV при необходимости.",
    },
    {
      title: "Проверьте предупреждения по качеству данных",
      description:
        params.qualityIssuesCount > 0 || params.anomalyCount > 0
          ? `Есть сигналы: качество данных — ${formatNumber(params.qualityIssuesCount, 0)}, аномалии — ${formatNumber(params.anomalyCount, 0)}.`
          : "Критичных замечаний по качеству данных и аномалиям не найдено.",
    },
  ];
}

function withApiBase(url: string) {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  return `${API_URL}${url}`;
}

function translateConfidence(value: string) {
  switch (value) {
    case "high":
      return "высокая";
    case "medium":
      return "средняя";
    case "low":
      return "низкая";
    case "insufficient_data":
      return "недостаточно данных";
    default:
      return value;
  }
}
