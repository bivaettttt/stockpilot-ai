"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { Boxes, CalendarRange, LineChart, Package, ShieldAlert } from "lucide-react";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { useI18n } from "@/src/i18n/provider";
import { formatCompactMoney, formatNumber } from "@/src/lib/format";

const copy = {
  ru: {
    title: "Товары",
    emptyDesc: "Категории, структура ассортимента и ключевые SKU будут доступны после анализа.",
    notStarted: "Анализ ещё не запущен",
    emptyTitle: "Товарная аналитика появится после анализа",
    emptyText: "Загрузите файл продаж и остатков, чтобы увидеть реальные категории, выручку, спрос и проблемные SKU.",
    upload: "Загрузить файл",
    pageDesc:
      "Страница показывает категории, товары и динамику из текущего анализа.",
    currentPeriod: "Период текущего анализа",
    noPeriod: "Нет данных о периоде",
    periodNote: "Все блоки ниже относятся к одному и тому же анализу, без частичного пересчёта только отдельных графиков.",
    sku: "SKU в анализе",
    categoriesCount: "Категорий",
    revenue: "Выручка категорий",
    risk: "SKU с риском дефицита",
    categories: "Категории",
    categoriesDesc: "Реальный вклад категорий из текущего анализа.",
    category: "Категория",
    sold: "Продано, ед.",
    topProducts: "Топ товары",
    topProductsDesc: "SKU с наибольшей выручкой по текущему анализу.",
    product: "Товар",
    stock: "Остаток",
    weekdays: "Продажи по дням недели",
    noWeekdays: "Нет среза по дням недели.",
    months: "Продажи по месяцам",
    noMonths: "Нет помесячного среза.",
  },
  en: {
    title: "Products",
    emptyDesc: "Categories, assortment structure and key SKUs appear after analysis.",
    notStarted: "Analysis has not started",
    emptyTitle: "Product analytics appears after analysis",
    emptyText: "Upload sales and stock data to see real categories, revenue, demand and problem SKUs.",
    upload: "Upload file",
    pageDesc:
      "This page shows the current analysis. The period switcher is hidden because partial-window recalculation is not implemented for every block yet.",
    currentPeriod: "Current analysis period",
    noPeriod: "No period data",
    periodNote: "All blocks below refer to the same analysis without recalculating only selected charts.",
    sku: "SKUs in analysis",
    categoriesCount: "Categories",
    revenue: "Category revenue",
    risk: "SKUs with stockout risk",
    categories: "Categories",
    categoriesDesc: "Real category contribution from the current analysis.",
    category: "Category",
    sold: "Sold, units",
    topProducts: "Top products",
    topProductsDesc: "SKUs with the highest revenue in the current analysis.",
    product: "Product",
    stock: "Stock",
    weekdays: "Sales by weekday",
    noWeekdays: "No weekday breakdown.",
    months: "Sales by month",
    noMonths: "No monthly breakdown.",
  },
} as const;

export default function AnalyticsPage() {
  const state = useDashboardState();
  const { locale } = useI18n();
  const text = copy[locale];
  const hasAnalysis = Boolean(state.result);

  const categorySales = useMemo(() => state.result?.category_sales ?? [], [state.result?.category_sales]);
  const topProducts = useMemo(() => state.result?.top_products ?? [], [state.result?.top_products]);
  const analytics = state.result?.analytics_snapshot ?? {};

  const weekdaySales = useMemo(() => (analytics.weekday_sales ?? []).slice(0, 7), [analytics.weekday_sales]);
  const monthlySales = useMemo(() => (analytics.monthly_sales ?? []).slice(0, 6), [analytics.monthly_sales]);
  const totalRevenue = useMemo(
    () => categorySales.reduce((sum, item) => sum + (item.total_revenue ?? 0), 0),
    [categorySales]
  );
  const maxCategoryRevenue = useMemo(
    () => Math.max(1, ...categorySales.map((item) => item.total_revenue ?? 0)),
    [categorySales]
  );
  const maxProductRevenue = useMemo(
    () => Math.max(1, ...topProducts.map((item) => item.total_revenue ?? 0)),
    [topProducts]
  );

  if (!hasAnalysis) {
    return (
      <div className="space-y-6">
        <PageTitle
          title={text.title}
          description={text.emptyDesc}
        />
        <Surface className="p-6">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1 text-sm text-[color:var(--muted)]">
              <Boxes className="h-4 w-4" />
              {text.notStarted}
            </div>
            <h2 className="text-2xl font-semibold">{text.emptyTitle}</h2>
            <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
              {text.emptyText}
            </p>
            <UiButton href="/overview#upload-panel">{text.upload}</UiButton>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageTitle
        title={text.title}
        description={text.pageDesc}
      />

      <Surface className="p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1 text-sm text-[color:var(--muted)]">
              <CalendarRange className="h-4 w-4" />
              {text.currentPeriod}
            </div>
            <p className="mt-2 text-sm text-[color:var(--muted)]">
              {state.datasetMeta?.startDate && state.datasetMeta?.endDate
                ? `${state.datasetMeta.startDate} - ${state.datasetMeta.endDate}`
                : text.noPeriod}
            </p>
          </div>
          <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-4 py-3 text-sm text-[color:var(--muted)]">
            {text.periodNote}
          </div>
        </div>
      </Surface>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={<Boxes className="h-5 w-5" />} title={text.sku} value={formatNumber(state.datasetMeta?.skuCount ?? 0, 0)} />
        <StatCard icon={<Package className="h-5 w-5" />} title={text.categoriesCount} value={formatNumber(categorySales.length, 0)} />
        <StatCard icon={<LineChart className="h-5 w-5" />} title={text.revenue} value={formatCompactMoney(totalRevenue)} />
        <StatCard icon={<ShieldAlert className="h-5 w-5" />} title={text.risk} value={formatNumber(state.stockoutCandidates.length, 0)} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Surface className="overflow-hidden p-0">
          <div className="border-b border-[color:var(--border)] px-5 py-4">
            <h2 className="text-base font-semibold">{text.categories}</h2>
            <p className="mt-1 text-sm text-[color:var(--muted)]">{text.categoriesDesc}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)]">
                <tr>
                  <th className="px-5 py-3 font-medium">{text.category}</th>
                  <th className="px-5 py-3 font-medium">{text.revenue}</th>
                  <th className="px-5 py-3 font-medium">{text.sold}</th>
                  <th className="px-5 py-3 font-medium">SKU</th>
                </tr>
              </thead>
              <tbody>
                {categorySales.map((item) => (
                  <tr key={item.category} className="border-t border-[color:var(--border)]">
                    <td className="px-5 py-3 font-medium">{item.category}</td>
                    <td className="px-5 py-3">
                      <div className="min-w-[9rem] space-y-1.5">
                        <div className="flex items-center justify-between gap-3">
                          <span>{formatCompactMoney(item.total_revenue)}</span>
                          <span className="text-xs text-[color:var(--muted)]">
                            {totalRevenue > 0 ? `${formatNumber(((item.total_revenue ?? 0) / totalRevenue) * 100, 0)}%` : "—"}
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-[color:var(--surface-muted)]">
                          <div
                            className="h-full rounded-full bg-[color:var(--accent)]"
                            style={{ width: `${Math.max(6, ((item.total_revenue ?? 0) / maxCategoryRevenue) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">{formatNumber(item.total_quantity_sold, 0)}</td>
                    <td className="px-5 py-3">{formatNumber(item.unique_products, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>

        <Surface className="overflow-hidden p-0">
          <div className="border-b border-[color:var(--border)] px-5 py-4">
            <h2 className="text-base font-semibold">{text.topProducts}</h2>
            <p className="mt-1 text-sm text-[color:var(--muted)]">{text.topProductsDesc}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)]">
                <tr>
                  <th className="px-5 py-3 font-medium">SKU</th>
                  <th className="px-5 py-3 font-medium">{text.product}</th>
                  <th className="px-5 py-3 font-medium">{text.revenue}</th>
                  <th className="px-5 py-3 font-medium">{text.stock}</th>
                </tr>
              </thead>
              <tbody>
                {topProducts.slice(0, 8).map((item) => (
                  <tr key={item.sku} className="border-t border-[color:var(--border)]">
                    <td className="px-5 py-3 font-medium">{item.sku}</td>
                    <td className="px-5 py-3">
                      <div className="max-w-[22rem] break-words">{item.product_name}</div>
                    </td>
                    <td className="px-5 py-3">
                      <div className="min-w-[8rem] space-y-1.5">
                        <span>{formatCompactMoney(item.total_revenue)}</span>
                        <div className="h-2 overflow-hidden rounded-full bg-[color:var(--surface-muted)]">
                          <div
                            className="h-full rounded-full bg-[color:var(--success)]"
                            style={{ width: `${Math.max(6, ((item.total_revenue ?? 0) / maxProductRevenue) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">{formatNumber(item.current_stock, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <Surface className="p-5">
          <h2 className="text-base font-semibold">{text.weekdays}</h2>
          <div className="mt-4 space-y-3">
            {weekdaySales.length > 0 ? weekdaySales.map((item, index) => {
              const revenue = Number(item.revenue ?? item.average_revenue ?? 0);
              const label = String(item.weekday ?? index + 1);
              const width = totalRevenue > 0 ? Math.min(100, (revenue / totalRevenue) * 100 * 6) : 0;
              return (
                <div key={label} className="space-y-1">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="text-[color:var(--muted)]">{label}</span>
                    <span>{formatCompactMoney(revenue)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[color:var(--surface-muted)]">
                    <div className="h-full rounded-full bg-[color:var(--accent)]" style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            }) : <p className="text-sm text-[color:var(--muted)]">{text.noWeekdays}</p>}
          </div>
        </Surface>

        <Surface className="p-5">
          <h2 className="text-base font-semibold">{text.months}</h2>
          <div className="mt-4 space-y-3">
            {monthlySales.length > 0 ? monthlySales.map((item, index) => {
              const revenue = Number(item.revenue ?? item.average_revenue ?? 0);
              const label = String(item.month ?? index + 1);
              const width = totalRevenue > 0 ? Math.min(100, (revenue / totalRevenue) * 100 * 6) : 0;
              return (
                <div key={label} className="space-y-1">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="text-[color:var(--muted)]">{label}</span>
                    <span>{formatCompactMoney(revenue)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[color:var(--surface-muted)]">
                    <div className="h-full rounded-full bg-[color:var(--accent)]" style={{ width: `${width}%` }} />
                  </div>
                </div>
              );
            }) : <p className="text-sm text-[color:var(--muted)]">{text.noMonths}</p>}
          </div>
        </Surface>
      </section>
    </div>
  );
}

function StatCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <Surface className="p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-[color:var(--surface-muted)] p-2.5">{icon}</div>
        <div>
          <p className="text-sm text-[color:var(--muted)]">{title}</p>
          <p className="mt-1 text-xl font-semibold">{value}</p>
        </div>
      </div>
    </Surface>
  );
}
