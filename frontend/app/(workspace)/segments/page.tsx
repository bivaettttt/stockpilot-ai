"use client";

import type { ReactNode } from "react";
import { useMemo } from "react";
import { Grid2x2, Info, Package, ShieldAlert, TrendingUp } from "lucide-react";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { useI18n } from "@/src/i18n/provider";
import { formatCompactMoney, formatNumber, formatPercent } from "@/src/lib/format";

const copy = {
  ru: {
    title: "Сегменты",
    desc: "ABC/XYZ сегментация для приоритизации ассортимента и контроля портфеля.",
    explanation: "ABC показывает вклад в выручку, XYZ — стабильность спроса. Используйте сегменты для приоритизации SKU.",
    emptyDesc: "ABC/XYZ сегментация помогает понять вклад в выручку и стабильность спроса.",
    notStarted: "Анализ ещё не запущен",
    emptyTitle: "Сегментация появится после анализа",
    emptyText: "StockPilot использует ABC для вклада в выручку и XYZ для стабильности спроса. Запустите анализ, чтобы получить сегменты по SKU.",
    upload: "Загрузить файл",
    insufficient: "Недостаточно данных",
    insufficientTitle: "Сегментация появится после анализа с достаточной историей продаж",
    insufficientText: "A/B/C показывает вклад в выручку, а X/Y/Z — стабильность спроса. Если истории мало, StockPilot не будет подменять это искусственными значениями.",
    skuInMatrix: "SKU в матрице",
    revenue: "Выручка",
    zClass: "SKU c Z-классом",
    topClass: "Самый частый сегмент",
    noData: "Нет данных",
    noRecommendation: "Нет рекомендации",
    howToRead: "Как читать ABC/XYZ",
    abcText: "A/B/C — вклад SKU в общую выручку.",
    xyzText: "X/Y/Z — стабильность спроса: от предсказуемого к нестабильному.",
    priorityText: "Товары AX обычно стоит держать под постоянным контролем, а CZ требуют осторожности из-за низкого вклада и нестабильного спроса.",
    classes: "Сегменты по классам",
    matrix: "Матрица ABC/XYZ",
    matrixDesc: "Сегменты строятся по текущему анализу без подстановки искусственных KPI.",
    product: "Товар",
    share: "Доля",
    stability: "Стабильность спроса",
    recommendation: "Рекомендация",
    class: "Класс",
  },
  en: {
    title: "Segments",
    desc: "ABC/XYZ segmentation for assortment prioritization and portfolio control.",
    explanation: "ABC shows revenue contribution, XYZ shows demand stability. Use segments to prioritize SKUs.",
    emptyDesc: "ABC/XYZ segmentation helps understand revenue contribution and demand stability.",
    notStarted: "Analysis has not started",
    emptyTitle: "Segmentation appears after analysis",
    emptyText: "StockPilot uses ABC for revenue contribution and XYZ for demand stability. Run an analysis to get SKU segments.",
    upload: "Upload file",
    insufficient: "Insufficient data",
    insufficientTitle: "Segmentation appears after analysis with enough sales history",
    insufficientText: "A/B/C shows revenue contribution, and X/Y/Z shows demand stability. If history is short, StockPilot will not show fake values.",
    skuInMatrix: "SKUs in matrix",
    revenue: "Revenue",
    zClass: "SKUs with Z class",
    topClass: "Most common segment",
    noData: "No data",
    noRecommendation: "No recommendation",
    howToRead: "How to read ABC/XYZ",
    abcText: "A/B/C is the SKU contribution to total revenue.",
    xyzText: "X/Y/Z is demand stability: from predictable to unstable.",
    priorityText: "AX products usually need close control, while CZ requires caution because contribution is low and demand is unstable.",
    classes: "Segments by class",
    matrix: "ABC/XYZ matrix",
    matrixDesc: "Segments are built from the current analysis without artificial KPIs.",
    product: "Product",
    share: "Share",
    stability: "Demand stability",
    recommendation: "Recommendation",
    class: "Class",
  },
} as const;

export default function SegmentsPage() {
  const state = useDashboardState();
  const { locale } = useI18n();
  const text = copy[locale];
  const matrix = useMemo(() => state.result?.abc_xyz_matrix ?? [], [state.result?.abc_xyz_matrix]);

  const summary = useMemo(() => {
    const totalRevenue = matrix.reduce((sum, item) => sum + (item.total_revenue ?? 0), 0);
    const criticalSegments = matrix.filter((item) => item.abc_xyz_class?.endsWith("Z")).length;
    const classCounts = matrix.reduce<Record<string, number>>((acc, item) => {
      const key = item.abc_xyz_class;
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});
    return {
      totalRevenue,
      criticalSegments,
      topClass: Object.entries(classCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? text.noData,
    };
  }, [matrix, text.noData]);

  if (!state.result) {
    return (
      <div className="space-y-6">
        <PageTitle
          title={text.title}
          description={text.emptyDesc}
        />
        <Surface className="p-6">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1 text-sm text-[color:var(--muted)]">
              <Grid2x2 className="h-4 w-4" />
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

  if (matrix.length === 0) {
    return (
      <div className="space-y-6">
        <PageTitle
          title={text.title}
          description={text.desc}
        />
        <Surface className="p-6">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--surface-muted)] px-3 py-1 text-sm text-[color:var(--muted)]">
              <Info className="h-4 w-4" />
              {text.insufficient}
            </div>
            <h2 className="text-2xl font-semibold">{text.insufficientTitle}</h2>
            <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
              {text.insufficientText}
            </p>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageTitle
        title={text.title}
        description={text.explanation}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={<Package className="h-5 w-5" />} title={text.skuInMatrix} value={formatNumber(matrix.length, 0)} />
        <StatCard icon={<TrendingUp className="h-5 w-5" />} title={text.revenue} value={formatCompactMoney(summary.totalRevenue)} />
        <StatCard icon={<ShieldAlert className="h-5 w-5" />} title={text.zClass} value={formatNumber(summary.criticalSegments, 0)} />
        <StatCard icon={<Grid2x2 className="h-5 w-5" />} title={text.topClass} value={summary.topClass} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Surface className="p-5">
          <h2 className="text-base font-semibold">{text.howToRead}</h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-[color:var(--muted)]">
            <p>
              <strong className="text-[color:var(--text)]">A/B/C</strong> — {text.abcText.replace(/^A\/B\/C (—|is) /, "")}
            </p>
            <p>
              <strong className="text-[color:var(--text)]">X/Y/Z</strong> — {text.xyzText.replace(/^X\/Y\/Z (—|is) /, "")}
            </p>
            <p>
              {text.priorityText}
            </p>
          </div>
        </Surface>

        <Surface className="overflow-hidden p-0">
          <div className="border-b border-[color:var(--border)] px-5 py-4">
            <h2 className="text-base font-semibold">{text.classes}</h2>
          </div>
          <div className="grid gap-px bg-[color:var(--border)] sm:grid-cols-3">
            {Object.entries(groupMatrixByClass(matrix)).map(([klass, items]) => (
              <div key={klass} className="bg-[color:var(--surface)] px-5 py-4">
                <p className="text-sm font-semibold">{klass}</p>
                <p className="mt-1 text-2xl font-semibold">{formatNumber(items.length, 0)}</p>
                <p className="mt-1 text-sm text-[color:var(--muted)]">
                  {items[0]?.management_action ?? text.noRecommendation}
                </p>
              </div>
            ))}
          </div>
        </Surface>
      </section>

      <Surface className="overflow-hidden p-0">
        <div className="border-b border-[color:var(--border)] px-5 py-4">
          <h2 className="text-base font-semibold">{text.matrix}</h2>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            {text.matrixDesc}
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-[980px] w-full text-sm">
            <thead className="bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)]">
              <tr>
                <th className="px-5 py-3 font-medium">SKU</th>
                <th className="px-5 py-3 font-medium">{text.product}</th>
                <th className="px-5 py-3 font-medium">ABC</th>
                <th className="px-5 py-3 font-medium">XYZ</th>
                <th className="px-5 py-3 font-medium">{text.class}</th>
                <th className="px-5 py-3 font-medium">{text.revenue}</th>
                <th className="px-5 py-3 font-medium">{text.share}</th>
                <th className="px-5 py-3 font-medium">{text.stability}</th>
                <th className="px-5 py-3 font-medium">{text.recommendation}</th>
              </tr>
            </thead>
            <tbody>
              {matrix.slice(0, 100).map((item) => (
                <tr key={item.sku} className="border-t border-[color:var(--border)] align-top">
                  <td className="px-5 py-3 font-medium">{item.sku}</td>
                  <td className="px-5 py-3">
                    <div className="max-w-[22rem] break-words">{item.product_name}</div>
                    <div className="mt-1 text-xs text-[color:var(--muted)]">{item.category}</div>
                  </td>
                  <td className="px-5 py-3">{item.abc_class}</td>
                  <td className="px-5 py-3">{item.xyz_class}</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-[color:var(--surface-muted)] px-2.5 py-1 text-xs font-medium">
                      {item.abc_xyz_class}
                    </span>
                  </td>
                  <td className="px-5 py-3">{formatCompactMoney(item.total_revenue)}</td>
                  <td className="px-5 py-3">{formatPercent(item.revenue_share_percent, 1)}</td>
                  <td className="px-5 py-3">
                    {Number.isFinite(item.coefficient_of_variation)
                      ? formatNumber(item.coefficient_of_variation, 2)
                      : text.noData}
                  </td>
                  <td className="px-5 py-3">
                    <div className="max-w-[18rem] break-words text-[color:var(--muted)]">{item.management_action}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Surface>
    </div>
  );
}

type SegmentMatrixItem = NonNullable<ReturnType<typeof useDashboardState>["result"]>["abc_xyz_matrix"][number];

function groupMatrixByClass(matrix: SegmentMatrixItem[]) {
  return matrix.reduce<Record<string, typeof matrix>>((acc, item) => {
    acc[item.abc_xyz_class] = [...(acc[item.abc_xyz_class] ?? []), item];
    return acc;
  }, {});
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
