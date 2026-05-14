"use client";

import { m, AnimatePresence } from "framer-motion";
import { X, Package, TrendingUp, AlertTriangle } from "lucide-react";
import { useI18n } from "@/src/i18n/provider";
import { Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { formatCompactMoney, formatNumber, formatPercent } from "@/src/lib/format";

interface SkuDetailDrawerProps {
  sku: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function SkuDetailDrawer({ sku, isOpen, onClose }: SkuDetailDrawerProps) {
  const { t } = useI18n();
  const state = useDashboardState();
  
  const skuData = state.filteredRecommendations.find(item => item.sku === sku);

  if (!skuData) return null;

  const riskLevel = skuData.stockout_risk ?? 0;
  const riskColor = riskLevel >= 0.7 ? "text-[color:var(--danger)]" : riskLevel >= 0.4 ? "text-[color:var(--warning)]" : "text-[color:var(--success)]";
  const riskLabel = riskLevel >= 0.7 ? "critical" : riskLevel >= 0.4 ? "medium" : "low";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm"
            onClick={onClose}
          />
          <m.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-md bg-[color:var(--surface)] shadow-xl"
          >
            <div className="flex h-full flex-col">
              <div className="flex items-center justify-between border-b border-[color:var(--border)] p-4">
                <h2 className="text-lg font-semibold">{skuData.sku}</h2>
                <UiButton variant="ghost" onClick={onClose} className="h-8 w-8 p-0">
                  <X className="h-4 w-4" />
                </UiButton>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Product Info */}
                <Surface className="p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-[color:var(--muted)]">
                    <Package className="h-4 w-4" />
                    {t("sku.details.product_info")}
                  </h3>
                  <div className="mt-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("table.product")}</span>
                      <span className="font-medium">{skuData.product_name}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("table.category")}</span>
                      <span className="font-medium">{skuData.category}</span>
                    </div>
                  </div>
                </Surface>

                {/* Risk Analysis */}
                <Surface className="p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-[color:var(--muted)]">
                    <AlertTriangle className="h-4 w-4" />
                    {t("sku.details.risk_analysis")}
                  </h3>
                  <div className="mt-3 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[color:var(--muted)]">{t("table.risk")}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${riskColor}`}>
                          {riskLabel.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium">
                          {formatPercent(riskLevel, 0)}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("sku.details.confidence")}</span>
                      <span className="font-medium">
                        {formatPercent(skuData.confidence_score ?? 0, 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("sku.details.priority")}</span>
                      <span className="font-medium capitalize">{skuData.priority}</span>
                    </div>
                  </div>
                </Surface>

                {/* Forecast */}
                <Surface className="p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-[color:var(--muted)]">
                    <TrendingUp className="h-4 w-4" />
                    {t("sku.details.forecast")}
                  </h3>
                  <div className="mt-3 space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("sku.details.recommended_qty")}</span>
                      <span className="font-medium">
                        {formatNumber(skuData.recommended_order_qty, 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("sku.details.expected_revenue")}</span>
                      <span className="font-medium">
                        {formatCompactMoney(skuData.expected_revenue ?? 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[color:var(--muted)]">{t("sku.details.stock_days")}</span>
                      <span className="font-medium">
                        {skuData.stock_days_left !== undefined 
                          ? typeof skuData.stock_days_left === 'number' 
                            ? formatNumber(skuData.stock_days_left, 0) 
                            : skuData.stock_days_left
                          : "N/A"}
                      </span>
                    </div>
                  </div>
                </Surface>

              </div>
            </div>
          </m.div>
        </>
      )}
    </AnimatePresence>
  );
}
