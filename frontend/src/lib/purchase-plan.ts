import type { Recommendation } from "@/src/types/api";

export type PurchasePlanStatus = "new" | "accepted" | "in_purchase" | "rejected" | "done";

export type PurchasePlanDecision = {
  status: PurchasePlanStatus;
  finalOrderQty: number | null;
  finalOrderQtyInput: string;
  comment: string;
};

export type PurchasePlanRow = Recommendation & {
  riskLevel: "high" | "medium" | "low";
  supplierLabel: string;
  reason: string;
  finalOrderQty: number | null;
  finalOrderQtyInput: string;
  comment: string;
  decisionStatus: PurchasePlanStatus;
  isQtyValid: boolean;
  estimatedCost: number | null;
};

export const PURCHASE_PLAN_STATUS_LABELS: Record<PurchasePlanStatus, string> = {
  new: "Новая",
  accepted: "Принято",
  in_purchase: "В закупке",
  rejected: "Отклонено",
  done: "Выполнено",
};

export function buildPurchasePlanStorageKey(params: {
  runId?: string | null;
  reportPath?: string | null;
  filename?: string | null;
  dateRangeDays?: number | null;
  skuCount?: number | null;
  totalRows?: number | null;
}) {
  if (params.runId?.trim()) {
    return `stockpilot_purchase_plan:run:${params.runId.trim()}`;
  }

  const stableParts = [
    params.reportPath ?? "",
    params.filename ?? "",
    String(params.dateRangeDays ?? ""),
    String(params.skuCount ?? ""),
    String(params.totalRows ?? ""),
  ]
    .map((part) => part.trim())
    .filter(Boolean);

  return `stockpilot_purchase_plan:${stableParts.join("|") || "default"}`;
}

export function loadPurchasePlanDecisions(storageKey: string): Record<string, PurchasePlanDecision> {
  if (typeof window === "undefined") {
    return {};
  }

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as Record<string, PurchasePlanDecision>;
    return parsed ?? {};
  } catch {
    return {};
  }
}

export function savePurchasePlanDecisions(
  storageKey: string,
  decisions: Record<string, PurchasePlanDecision>
) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(storageKey, JSON.stringify(decisions));
}

export function createDefaultDecision(recommendation: Recommendation): PurchasePlanDecision {
  const recommendedQty = Math.max(
    0,
    Math.round(recommendation.adjusted_order_qty ?? recommendation.recommended_order_qty ?? 0)
  );
  return {
    status: "new",
    finalOrderQty: recommendedQty,
    finalOrderQtyInput: String(recommendedQty),
    comment: "",
  };
}

export function normalizeDecision(
  recommendation: Recommendation,
  decision?: Partial<PurchasePlanDecision> | null
): PurchasePlanDecision {
  const fallback = createDefaultDecision(recommendation);
  const input = decision?.finalOrderQtyInput ?? String(decision?.finalOrderQty ?? fallback.finalOrderQty ?? "");
  const trimmedInput = input.trim();
  const parsedQty =
    trimmedInput === ""
      ? null
      : Number.isFinite(Number(trimmedInput))
        ? Number(trimmedInput)
        : null;

  return {
    status: isValidStatus(decision?.status) ? decision.status : fallback.status,
    finalOrderQty:
      parsedQty !== null && parsedQty >= 0 ? parsedQty : trimmedInput === "" ? null : fallback.finalOrderQty,
    finalOrderQtyInput: trimmedInput,
    comment: typeof decision?.comment === "string" ? decision.comment : fallback.comment,
  };
}

export function isValidStatus(value: unknown): value is PurchasePlanStatus {
  return value === "new" || value === "accepted" || value === "in_purchase" || value === "rejected" || value === "done";
}

export function buildPurchasePlanRows(
  recommendations: Recommendation[],
  decisions: Record<string, PurchasePlanDecision>
): PurchasePlanRow[] {
  return recommendations.map((recommendation) => {
    const decision = normalizeDecision(recommendation, decisions[recommendation.sku]);
    const trimmedInput = decision.finalOrderQtyInput.trim();
    const numericValue = trimmedInput === "" ? null : Number(trimmedInput);
    const isQtyValid =
      trimmedInput !== "" &&
      Number.isFinite(numericValue) &&
      numericValue !== null &&
      numericValue >= 0;
    const supplierLabel =
      recommendation.supplier_name?.trim() ||
      recommendation.supplier?.trim() ||
      "Поставщик не указан";
    const estimatedCost =
      typeof recommendation.estimated_cost === "number"
        ? recommendation.estimated_cost
        : typeof recommendation.purchase_price === "number" &&
      isQtyValid &&
      numericValue !== null
        ? recommendation.purchase_price * numericValue
        : null;

    return {
      ...recommendation,
      riskLevel: getRiskLevel(recommendation.stockout_risk ?? 0),
      supplierLabel,
      reason: recommendation.explanation?.trim() || recommendation.message || "Нет данных",
      finalOrderQty: isQtyValid && numericValue !== null ? numericValue : null,
      finalOrderQtyInput: decision.finalOrderQtyInput,
      comment: decision.comment,
      decisionStatus: decision.status,
      isQtyValid,
      estimatedCost,
    };
  });
}

export function exportPurchasePlanCsv(rows: PurchasePlanRow[]) {
  const today = new Date().toISOString().slice(0, 10);
  const filename = `stockpilot_purchase_plan_${today}.csv`;
  const headers = [
    "sku",
    "product_name",
    "category",
    "supplier",
    "supplier_lead_time_days",
    "moq",
    "pack_size",
    "current_stock",
    "recommended_order_qty",
    "system_recommended_qty",
    "adjusted_order_qty",
    "adjustment_reason",
    "final_order_qty",
    "status",
    "comment",
    "reason",
    "estimated_cost",
  ];

  const lines = [
    headers.join(","),
    ...rows.map((row) =>
      [
        row.sku,
        row.product_name,
        row.category,
        row.supplierLabel,
        row.supplier_lead_time_days ?? "",
        row.moq ?? "",
        row.pack_size ?? "",
        row.current_stock ?? "",
        row.recommended_order_qty ?? "",
        row.system_recommended_qty ?? row.recommended_order_qty ?? "",
        row.adjusted_order_qty ?? "",
        row.adjustment_reason ?? "",
        row.finalOrderQty ?? "",
        PURCHASE_PLAN_STATUS_LABELS[row.decisionStatus],
        row.comment,
        row.reason,
        row.estimatedCost ?? "",
      ]
        .map(toCsvCell)
        .join(",")
    ),
  ];

  const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8;" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

function toCsvCell(value: string | number) {
  const stringValue = String(value ?? "");
  const escaped = stringValue.replace(/"/g, '""');
  return `"${escaped}"`;
}

function getRiskLevel(stockoutRisk: number): "high" | "medium" | "low" {
  if (stockoutRisk >= 0.7) {
    return "high";
  }
  if (stockoutRisk >= 0.4) {
    return "medium";
  }
  return "low";
}
