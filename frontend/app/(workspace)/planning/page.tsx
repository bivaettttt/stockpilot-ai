"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, m } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Download,
  Eye,
  Package,
  Search,
  ShoppingCart,
  X,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { enrichProcurementPlanRequest } from "@/src/lib/api/suppliers";
import {
  getHistoryDecisionsRequest,
  putHistoryDecisionsRequest,
} from "@/src/lib/api/history";
import {
  buildPurchasePlanRows,
  buildPurchasePlanStorageKey,
  createDefaultDecision,
  exportPurchasePlanCsv,
  loadPurchasePlanDecisions,
  PURCHASE_PLAN_STATUS_LABELS,
  savePurchasePlanDecisions,
  type PurchasePlanDecision,
  type PurchasePlanRow,
  type PurchasePlanStatus,
} from "@/src/lib/purchase-plan";
import { formatCompactMoney, formatNumber, formatRisk } from "@/src/lib/format";
import { API_URL } from "@/src/lib/constants";
import { cn } from "@/src/lib/utils";

type StatusFilter = PurchasePlanStatus | "all";
type RiskFilter = "all" | "high" | "medium" | "low";
type ViewMode = "all_items" | "by_supplier";

export default function PlanningPage() {
  const state = useDashboardState();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [supplierFilter, setSupplierFilter] = useState("all");
  const [viewMode, setViewMode] = useState<ViewMode>("all_items");
  const [selectedSku, setSelectedSku] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [decisionDraftsByKey, setDecisionDraftsByKey] = useState<
    Record<string, Record<string, PurchasePlanDecision>>
  >({});

  const recommendations = useMemo(() => state.result?.recommendations ?? [], [state.result?.recommendations]);
  const hasAnalysis = recommendations.length > 0;
  const enrichQuery = useQuery({
    queryKey: ["procurement-enrich", state.activeRunId ?? state.result?.report_path ?? "active"],
    enabled: hasAnalysis,
    queryFn: () => enrichProcurementPlanRequest(recommendations),
  });
  const enrichedRecommendations = enrichQuery.data?.items ?? recommendations;
  const isEnriching = enrichQuery.isLoading || enrichQuery.isFetching;
  const storageKey = useMemo(
    () =>
      buildPurchasePlanStorageKey({
        runId: state.activeRunId,
        reportPath: state.result?.report_path ?? null,
        filename: state.activeAnalysisFilename ?? null,
        dateRangeDays: state.result?.summary_metrics.date_range_days ?? null,
        skuCount: state.result?.summary_metrics.unique_products ?? null,
        totalRows: state.result?.data_quality?.total_rows ?? state.datasetMeta?.totalRows ?? null,
      }),
    [
      state.datasetMeta?.totalRows,
      state.activeAnalysisFilename,
      state.activeRunId,
      state.result?.data_quality?.total_rows,
      state.result?.report_path,
      state.result?.summary_metrics,
    ]
  );
  const legacyStorageKey = useMemo(
    () =>
      buildPurchasePlanStorageKey({
        reportPath: state.result?.report_path ?? null,
        filename: state.activeAnalysisFilename ?? null,
        dateRangeDays: state.result?.summary_metrics.date_range_days ?? null,
        skuCount: state.result?.summary_metrics.unique_products ?? null,
        totalRows: state.result?.data_quality?.total_rows ?? state.datasetMeta?.totalRows ?? null,
      }),
    [
      state.datasetMeta?.totalRows,
      state.activeAnalysisFilename,
      state.result?.data_quality?.total_rows,
      state.result?.report_path,
      state.result?.summary_metrics,
    ]
  );

  const storedDecisions = useMemo(() => {
    if (!hasAnalysis) {
      return {};
    }
    const stored = loadPurchasePlanDecisions(storageKey);
    const legacyStored =
      storageKey !== legacyStorageKey ? loadPurchasePlanDecisions(legacyStorageKey) : {};
    return Object.fromEntries(
      enrichedRecommendations.map((recommendation) => [
        recommendation.sku,
        stored[recommendation.sku] ??
          legacyStored[recommendation.sku] ??
          createDefaultDecision(recommendation),
      ])
    );
  }, [enrichedRecommendations, hasAnalysis, legacyStorageKey, storageKey]);

  const decisions = decisionDraftsByKey[storageKey] ?? storedDecisions;

  useEffect(() => {
    if (!hasAnalysis) {
      return;
    }
    savePurchasePlanDecisions(storageKey, decisions);
  }, [decisions, hasAnalysis, storageKey]);

  useEffect(() => {
    if (!hasAnalysis) {
      return;
    }

    let cancelled = false;

    async function hydrateDecisions() {
      if (!state.activeRunId) {
        setDecisionDraftsByKey((current) =>
          current[storageKey]
            ? current
            : {
                ...current,
                [storageKey]: storedDecisions,
              }
        );
        return;
      }

      try {
        const response = await getHistoryDecisionsRequest(state.activeRunId);
        if (cancelled) {
          return;
        }

        const remoteDecisions = Object.fromEntries(
          enrichedRecommendations.map((recommendation) => [
            recommendation.sku,
            response.decisions[recommendation.sku] ?? storedDecisions[recommendation.sku] ?? createDefaultDecision(recommendation),
          ])
        ) as Record<string, PurchasePlanDecision>;

        setDecisionDraftsByKey((current) => ({
          ...current,
          [storageKey]: remoteDecisions,
        }));
      } catch {
        if (cancelled) {
          return;
        }
        setDecisionDraftsByKey((current) =>
          current[storageKey]
            ? current
            : {
                ...current,
                [storageKey]: storedDecisions,
              }
        );
      }
    }

    void hydrateDecisions();

    return () => {
      cancelled = true;
    };
  }, [enrichedRecommendations, hasAnalysis, state.activeRunId, storageKey, storedDecisions]);

  useEffect(() => {
    if (!hasAnalysis || !state.activeRunId) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void putHistoryDecisionsRequest(state.activeRunId as string, decisions).catch(() => {
        // Keep local state/localStorage as the safe fallback.
      });
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [decisions, hasAnalysis, state.activeRunId]);

  const rows = useMemo(() => buildPurchasePlanRows(enrichedRecommendations, decisions), [decisions, enrichedRecommendations]);
  const selectedRow = useMemo(
    () => rows.find((row) => row.sku === selectedSku) ?? null,
    [rows, selectedSku]
  );
  const lowReliabilityReasons = useMemo(
    () =>
      new Map(
        (state.analysisReliability?.sku_reliability ?? [])
          .filter((item) => item.confidence === "low")
          .map((item) => [item.sku, item.reason])
      ),
    [state.analysisReliability?.sku_reliability]
  );
  const supplierOptions = useMemo(() => {
    const values = Array.from(new Set(rows.map((row) => row.supplierLabel)));
    return values.sort((left, right) => left.localeCompare(right, "ru"));
  }, [rows]);
  const hasRealSupplierData = useMemo(
    () => rows.some((row) => row.supplierLabel !== "Поставщик не указан"),
    [rows]
  );

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return rows
      .filter((row) => {
        const matchesQuery =
          !normalizedQuery ||
          `${row.sku} ${row.product_name} ${row.category} ${row.supplierLabel}`
            .toLowerCase()
            .includes(normalizedQuery);
        const matchesStatus = statusFilter === "all" || row.decisionStatus === statusFilter;
        const matchesRisk = riskFilter === "all" || row.riskLevel === riskFilter;
        const matchesSupplier = supplierFilter === "all" || row.supplierLabel === supplierFilter;
        return matchesQuery && matchesStatus && matchesRisk && matchesSupplier;
      })
      .sort(comparePurchasePlanRows);
  }, [query, riskFilter, rows, statusFilter, supplierFilter]);

  const groupedRows = useMemo(() => {
    const groups = new Map<string, PurchasePlanRow[]>();
    for (const row of filteredRows) {
      const supplier = row.supplierLabel;
      const current = groups.get(supplier) ?? [];
      current.push(row);
      groups.set(supplier, current);
    }
    return Array.from(groups.entries()).map(([supplier, items]) => ({
      supplier,
      items,
      skuCount: items.length,
      totalFinalQty: items.reduce((sum, item) => sum + (item.finalOrderQty ?? 0), 0),
      estimatedCost: items.every((item) => item.estimatedCost != null)
        ? items.reduce((sum, item) => sum + (item.estimatedCost ?? 0), 0)
        : null,
      averageLeadTime:
        items.filter((item) => typeof item.supplier_lead_time_days === "number").length > 0
          ? items
              .filter((item) => typeof item.supplier_lead_time_days === "number")
              .reduce((sum, item) => sum + Number(item.supplier_lead_time_days ?? 0), 0) /
            items.filter((item) => typeof item.supplier_lead_time_days === "number").length
          : null,
      maxLeadTime: Math.max(0, ...items.map((item) => Number(item.supplier_lead_time_days ?? 0))),
    }));
  }, [filteredRows]);

  const invalidRows = rows.filter((row) => !row.isQtyValid);
  const stats = useMemo(
    () => ({
      urgent: rows.filter((row) => row.riskLevel === "high" && (row.finalOrderQty ?? 0) > 0).length,
      totalOrderQty: rows.reduce((sum, row) => sum + (row.finalOrderQty ?? 0), 0),
      accepted: rows.filter((row) => row.decisionStatus === "accepted" || row.decisionStatus === "in_purchase").length,
      withComments: rows.filter((row) => row.comment.trim() !== "").length,
    }),
    [rows]
  );

  function updateDecision(sku: string, partial: Partial<PurchasePlanDecision>) {
    const recommendation = enrichedRecommendations.find((item) => item.sku === sku);
    if (!recommendation) {
      return;
    }

    setDecisionDraftsByKey((current) => {
      const currentForKey = current[storageKey] ?? storedDecisions;
      const base = currentForKey[sku] ?? createDefaultDecision(recommendation);
      return {
        ...current,
        [storageKey]: {
          ...currentForKey,
          [sku]: {
            ...base,
            ...partial,
          },
        },
      };
    });
  }

  function exportPlan() {
    if (!hasAnalysis) {
      return;
    }
    if (invalidRows.length > 0) {
      toast.error("Исправьте итоговое количество перед экспортом плана.");
      return;
    }
    exportPurchasePlanCsv(filteredRows);
    toast.success("План закупок экспортирован в CSV.");
  }

  if (!hasAnalysis) {
    return (
      <div className="space-y-6">
        <PageTitle title="Закупочный план" description="Рабочий центр для решений по рекомендациям StockPilot." />
        <Surface className="p-6 md:p-7">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-md bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <ClipboardList className="h-4 w-4" />
              План пока пуст
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">Закупочный план появится после анализа</h2>
              <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                Загрузите файл продаж и остатков, чтобы StockPilot рассчитал, что нужно докупить, где есть риск дефицита и какие товары требуют внимания.
              </p>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <UiButton href="/overview#upload-panel" leadingIcon={<Package className="h-4 w-4" />}>
                Загрузить файл
              </UiButton>
              <a
                href={`${API_URL}/files/demo`}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
              >
                <ShoppingCart className="h-4 w-4" />
                Попробовать демо-файл
              </a>
            </div>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageTitle title="Закупочный план" description="Рабочая таблица для решений по заказу, статусам и комментариям." />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Срочно обработать"
          value={formatNumber(stats.urgent, 0)}
          description="позиций с высоким риском"
          tone="critical"
          icon={<AlertTriangle className="h-5 w-5" />}
        />
        <StatCard
          title="Итог к заказу"
          value={formatNumber(stats.totalOrderQty, 0)}
          description="единиц по текущим решениям"
          tone="neutral"
          icon={<Package className="h-5 w-5" />}
        />
        <StatCard
          title="Принято или в закупке"
          value={formatNumber(stats.accepted, 0)}
          description="позиции уже подтверждены"
          tone="success"
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
        <StatCard
          title="С комментариями"
          value={formatNumber(stats.withComments, 0)}
          description="позиции с заметками"
          tone="neutral"
          icon={<ClipboardList className="h-5 w-5" />}
        />
      </section>

      <Surface className="p-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-1 flex-wrap items-center gap-3">
            <label className="flex min-w-[260px] flex-1 items-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2">
              <Search className="h-4 w-4 text-[color:var(--muted)]" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Поиск по SKU, товару, категории"
                className="w-full bg-transparent text-sm outline-none"
                aria-label="Поиск по закупочному плану"
              />
            </label>

            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
              className="h-10 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-sm"
              aria-label="Фильтр по статусу"
            >
              <option value="all">Все статусы</option>
              {Object.entries(PURCHASE_PLAN_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value as RiskFilter)}
              className="h-10 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-sm"
              aria-label="Фильтр по риску"
            >
              <option value="all">Все уровни риска</option>
              <option value="high">Высокий риск</option>
              <option value="medium">Средний риск</option>
              <option value="low">Низкий риск</option>
            </select>

            {hasRealSupplierData ? (
              <select
                value={supplierFilter}
                onChange={(event) => setSupplierFilter(event.target.value)}
                className="h-10 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-sm"
                aria-label="Фильтр по поставщику"
              >
                <option value="all">Все поставщики</option>
                {supplierOptions.map((supplier) => (
                  <option key={supplier} value={supplier}>
                    {supplier}
                  </option>
                ))}
              </select>
            ) : null}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <UiButton href="/suppliers" variant="secondary">
              Поставщики
            </UiButton>
            <UiButton
              href="/copilot?q=Какие%20рекомендации%20требуют%20проверки%3F"
              variant="secondary"
            >
              Объяснить рекомендации
            </UiButton>
            <div className="inline-flex rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-1">
              <button
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm",
                  viewMode === "all_items" ? "bg-[color:var(--accent-soft)] text-[color:var(--text)]" : "text-[color:var(--muted)]"
                )}
                onClick={() => setViewMode("all_items")}
                type="button"
              >
                Все товары
              </button>
              <button
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm",
                  viewMode === "by_supplier" ? "bg-[color:var(--accent-soft)] text-[color:var(--text)]" : "text-[color:var(--muted)]"
                )}
                onClick={() => setViewMode("by_supplier")}
                type="button"
              >
                По поставщикам
              </button>
            </div>

            <UiButton
              variant="secondary"
              leadingIcon={<Download className="h-4 w-4" />}
              onClick={exportPlan}
              disabled={filteredRows.length === 0}
            >
              Экспортировать план
            </UiButton>
          </div>
        </div>

        {invalidRows.length > 0 ? (
          <div className="mt-3 rounded-lg border border-[color:var(--warning)] bg-[color:var(--warning-soft)] p-3 text-sm text-[color:var(--warning)]">
            Есть позиции с пустым или некорректным итоговым количеством. Исправьте их перед экспортом.
          </div>
        ) : null}

        {isEnriching ? (
          <div className="mt-3 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3 text-sm text-[color:var(--muted)]">
            Обновляем план с учётом поставщиков, MOQ и кратности упаковки.
          </div>
        ) : null}
      </Surface>

      {viewMode === "by_supplier" ? (
        <div className="space-y-4">
          {groupedRows.map((group) => (
            <Surface key={group.supplier} className="p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-base font-semibold">{group.supplier}</h2>
                  <p className="mt-1 text-sm text-[color:var(--muted)]">
                    SKU: {formatNumber(group.skuCount, 0)} • Итог к заказу: {formatNumber(group.totalFinalQty, 0)}
                    {group.estimatedCost != null ? ` • Примерная сумма: ${formatCompactMoney(group.estimatedCost)}` : " • Примерная сумма: Нет данных"}
                    {group.averageLeadTime != null ? ` • Средний срок поставки: ${formatNumber(group.averageLeadTime, 1)} дн.` : ""}
                    {group.maxLeadTime > 0 ? ` • Макс. срок: ${formatNumber(group.maxLeadTime, 0)} дн.` : ""}
                  </p>
                </div>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[color:var(--border)] text-left text-[color:var(--muted)]">
                      <th className="px-3 py-2 font-medium">SKU</th>
                      <th className="px-3 py-2 font-medium">Товар</th>
                      <th className="px-3 py-2 font-medium">Рекомендовано системой</th>
                      <th className="px-3 py-2 font-medium">С учётом поставщика</th>
                      <th className="px-3 py-2 font-medium">Итоговое количество</th>
                      <th className="px-3 py-2 font-medium">Статус решения</th>
                      <th className="px-3 py-2 font-medium">Комментарий</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.items.map((row) => (
                      <tr key={`${group.supplier}-${row.sku}`} className="border-b border-[color:var(--border)]">
                        <td className="px-3 py-2 font-medium">{row.sku}</td>
                        <td className="px-3 py-2">{row.product_name}</td>
                        <td className="px-3 py-2">{formatNumber(row.recommended_order_qty, 0)}</td>
                        <td className="px-3 py-2">{formatNumber(row.adjusted_order_qty ?? row.recommended_order_qty, 0)}</td>
                        <td className="px-3 py-2">{row.isQtyValid && row.finalOrderQty != null ? formatNumber(row.finalOrderQty, 0) : "Проверьте значение"}</td>
                        <td className="px-3 py-2">
                          <StatusBadge status={row.decisionStatus} />
                        </td>
                        <td className="px-3 py-2 text-[color:var(--muted)]">{row.comment.trim() || "Нет комментария"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Surface>
          ))}
        </div>
      ) : (
        <Surface className="overflow-hidden p-0">
          <div className="border-b border-[color:var(--border)] px-4 py-3 text-sm text-[color:var(--muted)]">
            Основная таблица показывает только поля решения. MOQ, упаковка, сроки поставки, причина корректировки и полный комментарий открываются в деталях строки.
          </div>
          <div className="max-h-[calc(100vh-15rem)] overflow-auto">
            <table className="min-w-[1080px] w-full text-sm">
              <thead className="sticky top-0 z-20 bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)] shadow-[inset_0_-1px_0_var(--border)]">
                <tr>
                  <th className="sticky left-0 z-30 min-w-[130px] bg-[color:var(--surface-muted)] px-4 py-3 font-medium">SKU</th>
                  <th className="sticky left-[130px] z-30 min-w-[240px] bg-[color:var(--surface-muted)] px-4 py-3 font-medium">Товар</th>
                  <th className="px-4 py-3 font-medium">Риск</th>
                  <th className="px-4 py-3 font-medium">Рекомендовано системой</th>
                  <th className="px-4 py-3 font-medium">С учётом поставщика</th>
                  <th className="px-4 py-3 font-medium">Итоговое количество</th>
                  <th className="px-4 py-3 font-medium">Статус решения</th>
                  <th className="px-4 py-3 font-medium">Комментарий</th>
                  <th className="px-4 py-3 font-medium">Детали</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.sku} className="border-t border-[color:var(--border)] align-top">
                    <td className="sticky left-0 z-10 bg-[color:var(--surface)] px-4 py-3 font-medium shadow-[inset_-1px_0_0_var(--border)]">
                      {row.sku}
                    </td>
                    <td className="sticky left-[130px] z-10 min-w-[240px] bg-[color:var(--surface)] px-4 py-3 shadow-[inset_-1px_0_0_var(--border)]">
                      <div className="font-medium">{row.product_name}</div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">
                        {row.category || "Нет категории"} • {row.priority ? `приоритет ${row.priority}` : "нет приоритета"}
                      </div>
                      {lowReliabilityReasons.has(row.sku) ? (
                        <div className="mt-2 inline-flex rounded-md bg-[color:var(--warning-soft)] px-2 py-1 text-xs font-medium text-[color:var(--warning)]">
                          Низкая надёжность
                        </div>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={row.riskLevel} value={row.stockout_risk ?? 0} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-[color:var(--accent)]">{formatNumber(row.recommended_order_qty, 0)}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold">{formatNumber(row.adjusted_order_qty ?? row.recommended_order_qty, 0)}</div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">
                        {row.adjustment_reason ? "Есть корректировка" : "Без ограничений"}
                      </div>
                    </td>
                    <td className="px-4 py-3 min-w-[170px]">
                      <input
                        type="number"
                        min={0}
                        step={1}
                        value={decisions[row.sku]?.finalOrderQtyInput ?? ""}
                        onChange={(event) =>
                          updateDecision(row.sku, {
                            finalOrderQtyInput: event.target.value,
                            finalOrderQty:
                              event.target.value.trim() === "" ? null : Math.max(0, Number(event.target.value)),
                          })
                        }
                        className={cn(
                          "h-10 w-full rounded-lg border px-3 text-sm outline-none",
                          row.isQtyValid
                            ? "border-[color:var(--border)] bg-[color:var(--surface)]"
                            : "border-[color:var(--danger)] bg-[color:var(--danger-soft)]"
                        )}
                        aria-label={`Итоговое количество для ${row.sku}`}
                      />
                      {!row.isQtyValid ? (
                        <p className="mt-1 text-xs text-[color:var(--danger)]">Введите количество 0 или больше</p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3 min-w-[150px]">
                      <StatusBadge status={decisions[row.sku]?.status ?? "new"} />
                    </td>
                    <td className="px-4 py-3 min-w-[130px]">
                      {row.comment.trim() ? (
                        <span className="rounded-full bg-[color:var(--accent-soft)] px-2.5 py-1 text-xs text-[color:var(--accent)]">
                          Есть
                        </span>
                      ) : (
                        <span className="text-xs text-[color:var(--muted)]">Нет</span>
                      )}
                    </td>
                    <td className="px-4 py-3 min-w-[120px]">
                      <div className="flex flex-col gap-2">
                        <UiButton
                          className="h-9 justify-start px-3"
                          variant="secondary"
                          leadingIcon={<Eye className="h-4 w-4" />}
                          onClick={() => {
                            setSelectedSku(row.sku);
                            setIsDrawerOpen(true);
                          }}
                        >
                          Детали
                        </UiButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
      )}

      {filteredRows.length === 0 ? (
        <Surface className="p-6 text-sm text-[color:var(--muted)]">
          По текущим фильтрам нет позиций. Измените фильтры или сбросьте поиск.
        </Surface>
      ) : null}

      <PlanningDetailDrawer
        row={selectedRow}
        isOpen={isDrawerOpen}
        reliabilityReason={selectedRow ? lowReliabilityReasons.get(selectedRow.sku) ?? null : null}
        decision={selectedRow ? decisions[selectedRow.sku] : undefined}
        onUpdate={updateDecision}
        onClose={() => {
          setSelectedSku(null);
          setIsDrawerOpen(false);
        }}
      />
    </div>
  );
}

function StatCard({
  title,
  value,
  description,
  tone,
  icon,
}: {
  title: string;
  value: string;
  description: string;
  tone: "critical" | "neutral" | "success";
  icon: React.ReactNode;
}) {
  const tones = {
    critical: "bg-[color:var(--danger-soft)] text-[color:var(--danger)]",
    neutral: "bg-[color:var(--surface-muted)] text-[color:var(--text)]",
    success: "bg-[color:var(--success-soft)] text-[color:var(--success)]",
  };

  return (
    <Surface className="p-4">
      <div className="flex items-center gap-3">
        <div className={cn("rounded-lg p-2.5", tones[tone])}>{icon}</div>
        <div>
          <p className="text-sm font-medium text-[color:var(--muted)]">{title}</p>
          <p className="text-xl font-bold">{value}</p>
          <p className="text-xs text-[color:var(--muted)]">{description}</p>
        </div>
      </div>
    </Surface>
  );
}

function RiskBadge({ level, value }: { level: "high" | "medium" | "low"; value: number }) {
  const styles = {
    high: "border-[color:var(--danger)] bg-[color:var(--danger-soft)] text-[color:var(--danger)]",
    medium: "border-[color:var(--warning)] bg-[color:var(--warning-soft)] text-[color:var(--warning)]",
    low: "border-[color:var(--success)] bg-[color:var(--success-soft)] text-[color:var(--success)]",
  };
  const labels = {
    high: "Высокий",
    medium: "Средний",
    low: "Низкий",
  };

  return (
    <div className="space-y-1">
      <span className={cn("inline-flex rounded-md border px-2 py-1 text-xs font-medium", styles[level])}>
        {labels[level]}
      </span>
      <div className="text-xs text-[color:var(--muted)]">{formatRisk(value)}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: PurchasePlanStatus }) {
  const styles = {
    new: "bg-[color:var(--surface-muted)] text-[color:var(--muted-strong)]",
    accepted: "bg-[color:var(--success-soft)] text-[color:var(--success)]",
    in_purchase: "bg-[color:var(--info-soft)] text-[color:var(--info)]",
    rejected: "bg-[color:var(--danger-soft)] text-[color:var(--danger)]",
    done: "bg-[color:var(--accent-soft)] text-[color:var(--accent)]",
  };
  const icons = {
    new: ClipboardList,
    accepted: CheckCircle2,
    in_purchase: ShoppingCart,
    rejected: XCircle,
    done: CheckCircle2,
  };
  const Icon = icons[status];

  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium", styles[status])}>
      <Icon className="h-3.5 w-3.5" />
      {PURCHASE_PLAN_STATUS_LABELS[status]}
    </span>
  );
}

function PlanningDetailDrawer({
  row,
  isOpen,
  reliabilityReason,
  decision,
  onUpdate,
  onClose,
}: {
  row: PurchasePlanRow | null;
  isOpen: boolean;
  reliabilityReason: string | null;
  decision?: PurchasePlanDecision;
  onUpdate: (sku: string, partial: Partial<PurchasePlanDecision>) => void;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {isOpen && row ? (
        <>
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/25 backdrop-blur-sm"
            onClick={onClose}
          />
          <m.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 32, stiffness: 320 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-[34rem] flex-col border-l border-[color:var(--line)] bg-[color:var(--surface)] shadow-[var(--shadow-hard)] backdrop-blur-2xl"
          >
            <div className="border-b border-[color:var(--line)] p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-semibold">{row.sku}</p>
                  <h2 className="mt-1 break-words text-xl font-semibold">{row.product_name}</h2>
                  <p className="mt-1 text-sm text-[color:var(--muted)]">{row.category || "Категория не указана"}</p>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-2 text-[color:var(--muted)]"
                  aria-label="Закрыть детали"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-5">
              <div className="grid grid-cols-2 gap-3">
                <DrawerMetric label="Рекомендовано системой" value={formatNumber(row.recommended_order_qty, 0)} />
                <DrawerMetric label="С учётом поставщика" value={formatNumber(row.adjusted_order_qty ?? row.recommended_order_qty, 0)} />
                <DrawerMetric label="Остаток" value={formatNumber(row.current_stock, 0)} />
                <DrawerMetric
                  label="Покрытие"
                  value={typeof row.days_of_cover === "number" ? `${formatNumber(row.days_of_cover, 1)} дн.` : String(row.stock_days_left || "Нет данных")}
                />
              </div>

              <section className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
                <h3 className="text-sm font-semibold">Решение по закупке</h3>
                <div className="mt-4 grid gap-3">
                  <label className="grid gap-1.5 text-sm">
                    <span className="text-[color:var(--muted)]">Итоговое количество</span>
                    <input
                      type="number"
                      min={0}
                      step={1}
                      value={decision?.finalOrderQtyInput ?? ""}
                      onChange={(event) =>
                        onUpdate(row.sku, {
                          finalOrderQtyInput: event.target.value,
                          finalOrderQty: event.target.value.trim() === "" ? null : Math.max(0, Number(event.target.value)),
                        })
                      }
                      className={cn(
                        "h-11 rounded-2xl border px-3 text-sm outline-none",
                        row.isQtyValid
                          ? "border-[color:var(--line)] bg-[color:var(--input-bg)]"
                          : "border-[color:var(--danger)] bg-[color:var(--danger-soft)]"
                      )}
                    />
                  </label>
                  <label className="grid gap-1.5 text-sm">
                    <span className="text-[color:var(--muted)]">Статус решения</span>
                    <select
                      value={decision?.status ?? "new"}
                      onChange={(event) => onUpdate(row.sku, { status: event.target.value as PurchasePlanStatus })}
                      className="h-11 rounded-2xl border border-[color:var(--line)] bg-[color:var(--input-bg)] px-3 text-sm outline-none"
                    >
                      {Object.entries(PURCHASE_PLAN_STATUS_LABELS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="grid gap-1.5 text-sm">
                    <span className="text-[color:var(--muted)]">Комментарий</span>
                    <textarea
                      value={decision?.comment ?? ""}
                      onChange={(event) => onUpdate(row.sku, { comment: event.target.value })}
                      placeholder="Например: проверить цену у поставщика"
                      className="min-h-[7rem] rounded-2xl border border-[color:var(--line)] bg-[color:var(--input-bg)] px-3 py-2 text-sm outline-none"
                    />
                  </label>
                </div>
              </section>

              <section className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
                <h3 className="text-sm font-semibold">Поставщик и ограничения</h3>
                <div className="mt-4 space-y-3 text-sm">
                  <DetailLine label="Поставщик" value={row.supplierLabel} note={formatSourceLabel(row.supplier_source)} />
                  <DetailLine label="Срок поставки" value={row.supplier_lead_time_days != null ? `${formatNumber(row.supplier_lead_time_days, 0)} дн.` : "Нет данных"} note={formatSourceLabel(row.lead_time_source)} />
                  <DetailLine label="Минимальный заказ" value={row.moq != null ? formatNumber(row.moq, 0) : "Нет данных"} note={formatSourceLabel(row.moq_source)} />
                  <DetailLine label="Кратность упаковки" value={row.pack_size != null ? formatNumber(row.pack_size, 0) : "Нет данных"} note={formatSourceLabel(row.pack_size_source)} />
                  <DetailLine label="Причина корректировки" value={row.adjustment_reason ?? "Без дополнительных ограничений"} />
                  <DetailLine label="Примерная сумма" value={row.estimatedCost != null ? formatCompactMoney(row.estimatedCost) : "Нет данных"} />
                </div>
              </section>

              <section className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
                <h3 className="text-sm font-semibold">Почему заказать</h3>
                <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{row.reason}</p>
                {reliabilityReason ? (
                  <div className="mt-4 rounded-2xl border border-[color:var(--warning)] bg-[color:var(--warning-soft)] p-3 text-sm text-[color:var(--warning)]">
                    Проверьте перед закупкой: {reliabilityReason}
                  </div>
                ) : null}
              </section>
            </div>
          </m.aside>
        </>
      ) : null}
    </AnimatePresence>
  );
}

function DrawerMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
      <p className="text-xs text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}

function DetailLine({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[color:var(--line)] pb-3 last:border-0 last:pb-0">
      <div>
        <p className="text-[color:var(--muted)]">{label}</p>
        {note ? <p className="mt-1 text-xs text-[color:var(--muted)]">{note}</p> : null}
      </div>
      <p className="max-w-[14rem] break-words text-right font-medium">{value}</p>
    </div>
  );
}

function comparePurchasePlanRows(left: PurchasePlanRow, right: PurchasePlanRow) {
  const riskWeight = { high: 3, medium: 2, low: 1 };
  const leftRisk = riskWeight[left.riskLevel];
  const rightRisk = riskWeight[right.riskLevel];
  if (leftRisk !== rightRisk) {
    return rightRisk - leftRisk;
  }

  const leftQty = left.finalOrderQty ?? 0;
  const rightQty = right.finalOrderQty ?? 0;
  if ((leftQty > 0) !== (rightQty > 0)) {
    return rightQty > 0 ? 1 : -1;
  }
  if (leftQty !== rightQty) {
    return rightQty - leftQty;
  }

  const leftPriority = priorityWeight(left.priority);
  const rightPriority = priorityWeight(right.priority);
  if (leftPriority !== rightPriority) {
    return rightPriority - leftPriority;
  }

  return left.sku.localeCompare(right.sku, "ru");
}

function formatSourceLabel(source: string | null | undefined) {
  if (source === "directory") {
    return "из справочника";
  }
  if (source === "file") {
    return "из файла";
  }
  return "не указано";
}

function priorityWeight(priority: string) {
  switch (priority) {
    case "critical":
      return 4;
    case "high":
      return 3;
    case "medium":
      return 2;
    case "low":
      return 1;
    default:
      return 0;
  }
}
