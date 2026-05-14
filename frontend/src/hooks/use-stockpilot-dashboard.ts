"use client";

import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getHistoryRequest,
  getHistoryResultRequest,
} from "@/src/lib/api/history";
import { runAnalysisRequest } from "@/src/lib/api/analysis";
import {
  inspectImportFile,
  normalizeImportFile,
  suggestImportMapping,
  uploadAndValidate,
  validateImportMapping,
} from "@/src/lib/api/upload";
import type {
  ActiveTab,
  AnalyzeResponse,
  ImportInspectResponse,
  MappingSuggestionItem,
  Recommendation,
  SuggestMappingResponse,
  ValidateFileResponse,
  ValidateMappingResponse,
} from "@/src/types/api";

type ActiveAnalysisSource = "current" | "history";

type PersistedActiveAnalysis = {
  result: AnalyzeResponse;
  source: ActiveAnalysisSource;
};

const ACTIVE_ANALYSIS_STORAGE_KEY = "stockpilot_active_analysis_v1";

function loadPersistedActiveAnalysis(): PersistedActiveAnalysis | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(ACTIVE_ANALYSIS_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as PersistedActiveAnalysis;
  } catch {
    return null;
  }
}

function persistActiveAnalysis(value: PersistedActiveAnalysis | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (!value) {
    window.localStorage.removeItem(ACTIVE_ANALYSIS_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(ACTIVE_ANALYSIS_STORAGE_KEY, JSON.stringify(value));
}

type FiltersState = {
  search: string;
  category: string;
  priority: string;
  action: string;
};

type PlanningSort =
  | "priority"
  | "risk"
  | "revenue"
  | "coverage";

const initialFilters: FiltersState = {
  search: "",
  category: "all",
  priority: "all",
  action: "all",
};

export function useStockpilotDashboard() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [horizon, setHorizon] = useState(30);
  const [safetyStock, setSafetyStock] = useState(0.25);
  const [leadTime, setLeadTime] = useState(5);

  const [validationResult, setValidationResult] =
    useState<ValidateFileResponse | null>(null);
  const [validationError, setValidationError] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [inspectResult, setInspectResult] = useState<ImportInspectResponse | null>(null);
  const [inspectError, setInspectError] = useState("");
  const [isInspecting, setIsInspecting] = useState(false);
  const [mappingSuggestion, setMappingSuggestion] = useState<SuggestMappingResponse | null>(null);
  const [mappingDraft, setMappingDraft] = useState<Record<string, MappingSuggestionItem>>({});
  const [mappingValidation, setMappingValidation] = useState<ValidateMappingResponse | null>(null);
  const [mappingError, setMappingError] = useState("");
  const [isSuggestingMapping, setIsSuggestingMapping] = useState(false);
  const [isValidatingMapping, setIsValidatingMapping] = useState(false);
  const [isNormalizingFile, setIsNormalizingFile] = useState(false);
  const [normalizedFile, setNormalizedFile] = useState<File | null>(null);

  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [activeAnalysisSource, setActiveAnalysisSource] = useState<ActiveAnalysisSource>("current");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");

  const [historyPage, setHistoryPage] = useState(1);
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);
  const [historyFileFilter, setHistoryFileFilter] = useState("");
  const [historyStatusFilter, setHistoryStatusFilter] = useState("all");

  const [filters, setFilters] = useState<FiltersState>(initialFilters);
  const [planningSort, setPlanningSort] = useState<PlanningSort>("priority");
  const [selectedSku, setSelectedSku] = useState<string | null>(null);
  const [historyCompareIds, setHistoryCompareIds] = useState<string[]>([]);
  const deferredSearch = useDeferredValue(filters.search);

  useEffect(() => {
    const restoredAnalysis = loadPersistedActiveAnalysis();
    if (!restoredAnalysis) {
      return;
    }

    startTransition(() => {
      setResult(restoredAnalysis.result);
      setActiveAnalysisSource(restoredAnalysis.source);
    });
  }, []);

  const historyQuery = useQuery({
    queryKey: [
      "history",
      historyPage,
      historyFileFilter,
      historyStatusFilter,
      historyRefreshToken,
    ],
    queryFn: () =>
      getHistoryRequest({
        page: historyPage,
        pageSize: 8,
        originalFilename: historyFileFilter || undefined,
        status: historyStatusFilter === "all" ? undefined : historyStatusFilter,
      }),
  });

  const history = historyQuery.data?.records ?? [];
  const historyPagination = historyQuery.data?.pagination ?? null;
  const historyError =
    historyQuery.error instanceof Error
      ? historyQuery.error.message
      : "";
  const isHistoryLoading = historyQuery.isLoading || historyQuery.isFetching;

  const validateMutation = useMutation({
    mutationFn: (target: File) => uploadAndValidate(target),
  });

  const inspectMutation = useMutation({
    mutationFn: (target: File) => inspectImportFile(target),
  });

  const suggestMappingMutation = useMutation({
    mutationFn: (target: File) => suggestImportMapping(target),
  });

  const validateMappingMutation = useMutation({
    mutationFn: (params: { file: File; mapping: Record<string, MappingSuggestionItem> }) =>
      validateImportMapping(params),
  });

  const normalizeMutation = useMutation({
    mutationFn: (params: { file: File; mapping: Record<string, MappingSuggestionItem> }) =>
      normalizeImportFile(params),
  });

  const analyzeMutation = useMutation({
    mutationFn: (params: { file: File; horizon: number; safetyStock: number; leadTime: number }) =>
      runAnalysisRequest(params),
  });

  function setActiveAnalysis(nextResult: AnalyzeResponse | null, source: ActiveAnalysisSource) {
    setResult(nextResult);
    setActiveAnalysisSource(source);
    persistActiveAnalysis(nextResult ? { result: nextResult, source } : null);
  }

  function handleFileChange(nextFile: File | null) {
    setFile(nextFile);
    setValidationResult(null);
    setValidationError("");
    setInspectResult(null);
    setInspectError("");
    setMappingSuggestion(null);
    setMappingDraft({});
    setMappingValidation(null);
    setMappingError("");
    setNormalizedFile(null);
    setActiveAnalysis(null, "current");
    setError("");
    setActiveTab("overview");
    setSelectedSku(null);
  }

  async function validateFile(targetFile?: File) {
    const fileToValidate = targetFile ?? file;
    if (!fileToValidate) {
      setValidationError("Сначала выберите CSV или XLSX-файл.");
      return;
    }

    if (targetFile) {
      setFile(targetFile);
    }

    setIsValidating(true);
    setValidationError("");
    setValidationResult(null);
    setError("");

    try {
      const response = await validateMutation.mutateAsync(fileToValidate);
      setValidationResult(response);
    } catch (validationRequestError) {
      setValidationError(
        validationRequestError instanceof Error
          ? validationRequestError.message
          : "Ошибка предварительной проверки файла."
      );
    } finally {
      setIsValidating(false);
    }
  }

  async function inspectFile(targetFile?: File) {
    const fileToInspect = targetFile ?? file;
    if (!fileToInspect) {
      setInspectError("Сначала выберите CSV или XLSX-файл.");
      return;
    }

    if (targetFile) {
      setFile(targetFile);
    }

    setIsInspecting(true);
    setInspectError("");
    setInspectResult(null);
    setValidationResult(null);
    setValidationError("");
    setMappingSuggestion(null);
    setMappingDraft({});
    setMappingValidation(null);
    setMappingError("");
    setNormalizedFile(null);
    setError("");

    try {
      const response = await inspectMutation.mutateAsync(fileToInspect);
      setInspectResult(response);
      if (!response.is_ready_for_analysis) {
        setIsSuggestingMapping(true);
        try {
          const suggested = await suggestMappingMutation.mutateAsync(fileToInspect);
          setMappingSuggestion(suggested);
          setMappingDraft(suggested.suggested_mapping);
        } catch (mappingSuggestError) {
          setMappingError(
            mappingSuggestError instanceof Error
              ? mappingSuggestError.message
              : "Не удалось подобрать сопоставление колонок."
          );
        } finally {
          setIsSuggestingMapping(false);
        }
      }
    } catch (inspectRequestError) {
      setInspectError(
        inspectRequestError instanceof Error
          ? inspectRequestError.message
          : "Не удалось прочитать структуру файла."
      );
    } finally {
      setIsInspecting(false);
    }
  }

  async function runAnalysis() {
    const fileToAnalyze = normalizedFile ?? file;
    if (!fileToAnalyze) {
      setError("Выберите CSV или XLSX-файл для анализа.");
      return;
    }

    if (!inspectResult?.is_ready_for_analysis && !normalizedFile) {
      setError("Перед анализом файл должен пройти предварительный просмотр структуры.");
      return;
    }

    setIsLoading(true);
    setError("");
    setActiveAnalysis(null, "current");
    setActiveTab("overview");

    try {
      const response = await analyzeMutation.mutateAsync({
        file: fileToAnalyze,
        horizon,
        safetyStock,
        leadTime,
      });

      startTransition(() => {
        setActiveAnalysis(response, "current");
        setActiveTab("overview");
      });

      setHistoryPage(1);
      setHistoryRefreshToken((current) => current + 1);
      void queryClient.invalidateQueries({ queryKey: ["history"] });
    } catch (analysisError) {
      setError(
        analysisError instanceof Error
          ? analysisError.message
          : "Не удалось выполнить анализ."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function validateSuggestedMapping() {
    if (!file) {
      setMappingError("Сначала выберите файл.");
      return;
    }

    setIsValidatingMapping(true);
    setMappingError("");
    setMappingValidation(null);
    setNormalizedFile(null);

    try {
      const response = await validateMappingMutation.mutateAsync({
        file,
        mapping: mappingDraft,
      });
      setMappingValidation(response);
    } catch (mappingValidationError) {
      setMappingError(
        mappingValidationError instanceof Error
          ? mappingValidationError.message
          : "Не удалось проверить сопоставление колонок."
      );
    } finally {
      setIsValidatingMapping(false);
    }
  }

  async function normalizeMappedFile() {
    if (!file) {
      setMappingError("Сначала выберите файл.");
      return;
    }

    if (!mappingValidation?.is_valid) {
      setMappingError("Сначала проверьте сопоставление колонок.");
      return;
    }

    setIsNormalizingFile(true);
    setMappingError("");

    try {
      const nextNormalizedFile = await normalizeMutation.mutateAsync({
        file,
        mapping: mappingDraft,
      });
      setNormalizedFile(nextNormalizedFile);
    } catch (normalizationError) {
      setMappingError(
        normalizationError instanceof Error
          ? normalizationError.message
          : "Не удалось нормализовать файл."
      );
    } finally {
      setIsNormalizingFile(false);
    }
  }

  function updateMappingField(field: string, sourceColumn: string | null) {
    setMappingDraft((current) => ({
      ...current,
      [field]: {
        source_column: sourceColumn,
        confidence: sourceColumn ? current[field]?.confidence ?? 1 : 0,
        status: sourceColumn ? "matched" : "missing",
      },
    }));
    setMappingValidation(null);
    setMappingError("");
    setNormalizedFile(null);
  }

  async function openHistoryRun(runId: string) {
    const snapshot = await getHistoryResultRequest(runId);

    setFile(null);
    setValidationResult(null);
    setValidationError("");
    setInspectResult(null);
    setInspectError("");
    setMappingSuggestion(null);
    setMappingDraft({});
    setMappingValidation(null);
    setMappingError("");
    setNormalizedFile(null);
    setError("");
    setSelectedSku(null);

    startTransition(() => {
      setActiveAnalysis(snapshot, "history");
      setActiveTab("overview");
    });
  }

  const recommendations = result?.recommendations ?? [];
  const filteredRecommendations = recommendations
    .filter((item) => {
    const matchesSearch =
      !deferredSearch ||
      `${item.sku} ${item.product_name} ${item.category}`
        .toLowerCase()
        .includes(deferredSearch.toLowerCase());
    const matchesCategory =
      filters.category === "all" || item.category === filters.category;
    const matchesPriority =
      filters.priority === "all" || item.priority === filters.priority;
    const matchesAction =
      filters.action === "all" || item.action_group === filters.action;

      return matchesSearch && matchesCategory && matchesPriority && matchesAction;
    })
    .sort((left, right) => {
      if (planningSort === "risk") {
        return (right.stockout_risk ?? 0) - (left.stockout_risk ?? 0);
      }

      if (planningSort === "revenue") {
        return (right.expected_revenue ?? 0) - (left.expected_revenue ?? 0);
      }

      if (planningSort === "coverage") {
        const leftCover =
          typeof left.stock_days_left === "number" ? left.stock_days_left : Number.POSITIVE_INFINITY;
        const rightCover =
          typeof right.stock_days_left === "number" ? right.stock_days_left : Number.POSITIVE_INFINITY;
        return leftCover - rightCover;
      }

      return 0;
    });

  const urgentRecommendations = filteredRecommendations.filter((item) =>
    ["critical", "high"].includes(item.priority)
  );

  const purchaseRecommendations = filteredRecommendations.filter(
    (item) => item.recommended_order_qty > 0
  );

  const selectedCategories = Array.from(
    new Set(recommendations.map((item) => item.category))
  ).sort((left, right) => left.localeCompare(right, "ru"));

  const selectedSkuDetails =
    filteredRecommendations.find((item) => item.sku === selectedSku) ??
    filteredRecommendations[0] ??
    result?.recommendations.find((item) => item.sku === selectedSku) ??
    result?.recommendations[0] ??
    null;

  const stockoutCandidates = recommendations
    .filter((item) => (item.stockout_risk ?? 0) >= 0.55)
    .slice(0, 6);
  const overstockCandidates = recommendations
    .filter((item) => (item.overstock_risk ?? 0) >= 0.55)
    .slice(0, 6);
  const anomalyFeed = (result?.analytics_snapshot?.demand_anomalies ?? []).slice(0, 8);
  const datasetMeta = result
    ? {
        startDate: result.daily_sales[0]?.date ?? null,
        endDate: result.daily_sales.at(-1)?.date ?? null,
        totalRows: result.data_quality?.total_rows ?? 0,
        skuCount: result.summary_metrics.unique_products ?? 0,
        categoryCount: result.summary_metrics.unique_categories ?? 0,
        historySpanDays: result.summary_metrics.date_range_days ?? 0,
      }
    : null;

  const analysisReliability = result?.analysis_reliability ?? null;
  const activeRunId = result?.run_id ?? null;
  const activeAnalysisFilename = result?.original_filename ?? file?.name ?? null;
  const activeAnalysisCreatedAt = result?.created_at ?? null;
  const isHistoryAnalysis = activeAnalysisSource === "history";
  const isDemoAnalysis = /demo|sample/i.test(activeAnalysisFilename ?? "");
  const reliabilitySummary = analysisReliability
    ? {
        dataQualityScore: analysisReliability.data_quality.score ?? null,
        dataQualityLabel: analysisReliability.data_quality.label,
        overallConfidence: analysisReliability.forecast_quality.overall_confidence,
        warningCount:
          (analysisReliability.data_quality.warnings?.length ?? 0) +
          (analysisReliability.forecast_quality.warnings?.length ?? 0) +
          (analysisReliability.warnings?.length ?? 0),
        lowConfidenceSkuCount: analysisReliability.sku_reliability.filter(
          (item) => item.confidence === "low"
        ).length,
      }
    : null;

  const summary = {
    totalExpectedRevenue: purchaseRecommendations.reduce(
      (sum, item) => sum + (item.expected_revenue ?? 0),
      0
    ),
    totalRecommendedUnits: purchaseRecommendations.reduce(
      (sum, item) => sum + (item.recommended_order_qty ?? 0),
      0
    ),
    urgentCount: urgentRecommendations.length,
    overstockCount: recommendations.filter(
      (item) => (item.overstock_risk ?? 0) >= 0.55
    ).length,
    medianConfidence:
      result?.product_forecast.length
        ? result.product_forecast
            .map((item) => item.confidence_score ?? 0)
            .sort((left, right) => left - right)[
            Math.floor(result.product_forecast.length / 2)
          ] ?? 0
        : 0,
  };

  const advancedRiskQueue = filteredRecommendations
    .map((item) => {
      const operationalRisk = (item.stockout_risk ?? 0) * 0.45;
      const financialRisk = Math.min((item.expected_revenue ?? 0) / 100000, 1) * 0.2;
      const forecastRisk = (1 - (item.confidence_score ?? 0) / 100) * 0.2;
      const volatilityRisk = item.demand_pattern === "volatile" ? 0.15 : 0.05;
      const composite = Math.min(1, operationalRisk + financialRisk + forecastRisk + volatilityRisk);

      return {
        ...item,
        operational_risk: operationalRisk,
        financial_risk: financialRisk,
        forecast_risk: forecastRisk,
        demand_volatility_risk: volatilityRisk,
        composite_risk: composite,
        weak_forecast: (item.confidence_score ?? 0) < 55,
        urgency_level: composite >= 0.7 ? "critical" : composite >= 0.5 ? "high" : composite >= 0.3 ? "medium" : "low",
      };
    })
    .sort((a, b) => b.composite_risk - a.composite_risk);

  const forecastGovernance = (result?.product_forecast ?? []).map((item) => ({
    ...item,
    weak_forecast: (item.confidence_score ?? 0) < 55,
    unstable_demand: item.demand_pattern === "volatile" || item.demand_pattern === "intermittent",
    intervention_required:
      (item.confidence_score ?? 0) < 55 ||
      item.demand_pattern === "volatile" ||
      item.demand_pattern === "intermittent",
  }));

  function selectSku(sku: string) {
    setSelectedSku(sku);
  }

  function applyRunPreset(record: { horizon: number; safety_stock: number; lead_time: number }) {
    setHorizon(record.horizon);
    setSafetyStock(record.safety_stock);
    setLeadTime(record.lead_time);
    setActiveTab("overview");
  }

  function toggleCompareRun(recordId: string) {
    setHistoryCompareIds((current) => {
      if (current.includes(recordId)) {
        return current.filter((value) => value !== recordId);
      }

      const next = [...current, recordId].slice(-2);
      return next;
    });
  }

  const comparedRuns = history.filter((record) => historyCompareIds.includes(record.id));
  const historyCompareSummary =
    comparedRuns.length === 2
      ? {
          revenueDelta:
            (comparedRuns[0].summary_metrics.total_revenue ?? 0) -
            (comparedRuns[1].summary_metrics.total_revenue ?? 0),
          marginDelta:
            (comparedRuns[0].summary_metrics.gross_margin_percent ?? 0) -
            (comparedRuns[1].summary_metrics.gross_margin_percent ?? 0),
          recommendationDelta:
            comparedRuns[0].recommendations_count - comparedRuns[1].recommendations_count,
        }
      : null;

  return {
    file,
    horizon,
    safetyStock,
    leadTime,
    validationResult,
    validationError,
    isValidating,
    inspectResult,
    inspectError,
    isInspecting,
    mappingSuggestion,
    mappingDraft,
    mappingValidation,
    mappingError,
    isSuggestingMapping,
    isValidatingMapping,
    isNormalizingFile,
    normalizedFile,
    result,
    activeRunId,
    activeAnalysisFilename,
    activeAnalysisCreatedAt,
    activeAnalysisSource,
    isHistoryAnalysis,
    isDemoAnalysis,
    error,
    isLoading,
    activeTab,
    history,
    historyError,
    historyPagination,
    historyPage,
    historyFileFilter,
    historyStatusFilter,
    isHistoryLoading,
    filters,
    planningSort,
    selectedSku,
    historyCompareIds,
    comparedRuns,
    historyCompareSummary,
    filteredRecommendations,
    purchaseRecommendations,
    urgentRecommendations,
    selectedCategories,
    selectedSkuDetails,
    stockoutCandidates,
    overstockCandidates,
    anomalyFeed,
    datasetMeta,
    analysisReliability,
    reliabilitySummary,
    summary,
    advancedRiskQueue,
    forecastGovernance,
    setHorizon,
    setSafetyStock,
    setLeadTime,
    setActiveTab,
    setHistoryPage,
    setHistoryFileFilter,
    setHistoryStatusFilter,
    setFilters,
    setPlanningSort,
    handleFileChange,
    inspectFile,
    updateMappingField,
    validateFile,
    validateSuggestedMapping,
    normalizeMappedFile,
    runAnalysis,
    openHistoryRun,
    reloadHistory: () => setHistoryRefreshToken((current) => current + 1),
    selectSku,
    applyRunPreset,
    toggleCompareRun,
  };
}

export type DashboardState = ReturnType<typeof useStockpilotDashboard>;

export function getTopRecommendations(
  recommendations: Recommendation[],
  limit = 8
) {
  return recommendations.slice(0, limit);
}
