"use client";

import {
  Area,
  AreaChart,
  Bar,
  Cell,
  ComposedChart,
  Line,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Scatter,
  ScatterChart,
  Treemap,
  ReferenceLine,
  type TooltipValueType,
  type TreemapNode,
} from "recharts";
import { ChartShell } from "@/src/components/app/chart-shell";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { formatCompactMoney, formatNumber, formatPercent } from "@/src/lib/format";
import type { AnalyticsSnapshot } from "@/src/types/api";

type ChartName = string | number;

function chartColors() {
  return {
    grid: "var(--border)",
    axis: "var(--muted)",
    primary: "var(--accent)",
    secondary: "#10b981",
    tertiary: "#f59e0b",
    quaternary: "#8b5cf6",
    quinary: "#ef4444",
    success: "#10b981",
    warning: "#f59e0b",
    danger: "#ef4444",
    info: "#3b82f6",
    fillPrimary: "color-mix(in srgb, var(--accent) 20%, transparent)",
    fillSecondary: "color-mix(in srgb, #10b981 20%, transparent)",
    fillTertiary: "color-mix(in srgb, #f59e0b 20%, transparent)",
    fillQuaternary: "color-mix(in srgb, #8b5cf6 20%, transparent)",
    fillQuinary: "color-mix(in srgb, #ef4444 20%, transparent)",
  };
}

// Multi-line Demand & Revenue Chart
export function DemandRevenueChart({ period = 30 }: { period?: number }) {
  const state = useDashboardState();
  const c = chartColors();
  const forecastByDate = (state.result?.daily_forecast_chart_data ?? []).reduce<Record<string, number>>(
    (acc, point) => {
      acc[point.date] = (acc[point.date] ?? 0) + point.predicted_quantity;
      return acc;
    },
    {}
  );
  const historicalData =
    state.result?.daily_sales?.slice(-period).map((point) => ({
      date: point.date.slice(5),
      demand: point.quantity_sold,
      revenue: point.revenue / 1000,
      forecast: null as number | null,
      upperBound: point.quantity_sold * 1.2,
      lowerBound: point.quantity_sold * 0.8,
    })) ?? [];
  const forecastData = Object.entries(forecastByDate).map(([date, forecast]) => ({
    date: date.slice(5),
    demand: null as number | null,
    revenue: null as number | null,
    forecast,
    upperBound: forecast * 1.2,
    lowerBound: forecast * 0.8,
  }));
  const data = [...historicalData, ...forecastData];

  if (!data.length) {
    return <EmptyChart message="No demand data available" />;
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis dataKey="date" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis yAxisId="left" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis yAxisId="right" orientation="right" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${c.grid}`, background: "var(--surface)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }} />
          <Legend />
          <Area yAxisId="left" type="monotone" dataKey="lowerBound" stroke="none" fill={c.fillQuinary} />
          <Area yAxisId="left" type="monotone" dataKey="upperBound" stroke="none" fill={c.fillQuinary} />
          <Line yAxisId="left" type="monotone" dataKey="forecast" stroke={c.secondary} strokeDasharray="5 5" strokeWidth={2} dot={false} name="Forecast" />
          <Line yAxisId="left" type="monotone" dataKey="demand" stroke={c.primary} strokeWidth={3} dot={false} name="Demand" />
          <Bar yAxisId="right" dataKey="revenue" fill={c.tertiary} opacity={0.6} name="Revenue ($k)" />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Category Performance Treemap
export function CategoryTreemap() {
  const state = useDashboardState();
  const c = chartColors();
  
  const data = state.result?.category_sales?.map((item, index) => ({
    name: item.category,
    size: item.total_revenue,
    fill: [c.primary, c.secondary, c.tertiary, c.quaternary, c.quinary][index % 5],
  })) ?? [];

  if (!data.length) {
    return <EmptyChart message="No category data available" />;
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          aspectRatio={4/3}
          stroke={c.grid}
          content={({ x, y, width, height, name, fill }: TreemapNode) => (
            <g>
              <rect x={x} y={y} width={width} height={height} style={{ fill: String(fill), stroke: c.grid, strokeWidth: 2, rx: 4 }} />
              {width > 50 && height > 30 && (
                <>
                  <text x={x + width / 2} y={y + height / 2 - 8} fill="white" textAnchor="middle" fontSize={12} fontWeight="bold">
                    {name}
                  </text>
                  <text x={x + width / 2} y={y + height / 2 + 8} fill="white" textAnchor="middle" fontSize={10}>
                    ${formatNumber(data.find(d => d.name === name)?.size || 0, 0)}
                  </text>
                </>
              )}
            </g>
          )}
        />
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Inventory Health Radar Chart
export function InventoryHealthRadar() {
  const c = chartColors();
  const state = useDashboardState();
  const recommendations = state.result?.recommendations ?? [];
  const stockAvailability =
    recommendations.length > 0
      ? (recommendations.filter((item) => (item.current_stock ?? 0) > 0).length / recommendations.length) * 100
      : 0;
  const averageStockoutRisk =
    recommendations.length > 0
      ? recommendations.reduce((sum, item) => sum + (item.stockout_risk ?? 0), 0) / recommendations.length
      : 0;
  const numericCoverageDays = recommendations
    .map((item) => item.days_of_cover)
    .filter((value): value is number => typeof value === "number");
  const averageCoverageDays =
    numericCoverageDays.length > 0
      ? numericCoverageDays.reduce((sum, value) => sum + value, 0) / numericCoverageDays.length
      : 0;
  const turnoverRatio = state.result?.summary_metrics.inventory_turnover_ratio ?? 0;

  const data = [
    { metric: "Stock Levels", value: Math.min(100, stockAvailability), fullMark: 100 },
    { metric: "Turnover Rate", value: Math.min(100, turnoverRatio * 20), fullMark: 100 },
    { metric: "Сигнал спроса", value: Math.min(100, state.summary.medianConfidence), fullMark: 100 },
    { metric: "Supply Risk", value: Math.min(100, averageStockoutRisk * 100), fullMark: 100 },
    { metric: "Coverage Days", value: Math.min(100, averageCoverageDays * 5), fullMark: 100 },
    { metric: "Надёжность прогноза", value: Math.min(100, state.summary.medianConfidence), fullMark: 100 },
  ];

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <PolarGrid stroke={c.grid} />
          <PolarAngleAxis dataKey="metric" tick={{ fill: c.axis, fontSize: 11 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: c.axis, fontSize: 10 }} />
          <Radar name="Health Score" dataKey="value" stroke={c.primary} fill={c.fillPrimary} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Stockout Risk Heatmap
export function StockoutRiskHeatmap() {
  const state = useDashboardState();
  const c = chartColors();
  
  const data = state.result?.recommendations?.slice(0, 20).map((item) => ({
    sku: item.sku,
    risk: (item.stockout_risk ?? 0) * 100,
    revenue: item.expected_revenue / 1000,
    category: item.category,
  })) ?? [];

  if (!data.length) {
    return <EmptyChart message="No risk data available" />;
  }

  const getRiskColor = (risk: number) => {
    if (risk > 70) return c.danger;
    if (risk > 40) return c.warning;
    return c.success;
  };

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 16, right: 8, bottom: 60, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis 
            dataKey="sku" 
            tick={{ fill: c.axis, fontSize: 10 }} 
            angle={-45} 
            textAnchor="end" 
            height={80}
          />
          <YAxis tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip 
            contentStyle={{ borderRadius: 12, border: `1px solid ${c.grid}`, background: "var(--surface)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
            formatter={(value: TooltipValueType | undefined, name: ChartName | undefined) => {
              if (typeof value !== "number") return [value, name];
              if (name === "risk") return [`${value.toFixed(1)}%`, "Риск дефицита"];
              if (name === "revenue") return [`$${value.toFixed(1)}k`, "Ожидаемая выручка"];
              return [value, name];
            }}
          />
          <Scatter data={data} fill={c.primary}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getRiskColor(entry.risk)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Pareto Analysis Chart
export function ParetoChart() {
  const state = useDashboardState();
  const c = chartColors();
  
  const sortedData = [...(state.result?.top_products || [])]
    .sort((a, b) => b.total_revenue - a.total_revenue)
    .slice(0, 10);
  
  const totalRevenue = sortedData.reduce((sum, item) => sum + item.total_revenue, 0);
  const data = sortedData.map((item, index) => {
    const cumulativeRevenue = sortedData
      .slice(0, index + 1)
      .reduce((sum, currentItem) => sum + currentItem.total_revenue, 0);

    return {
      sku: item.sku,
      revenue: item.total_revenue / 1000,
      cumulative: totalRevenue > 0 ? (cumulativeRevenue / totalRevenue) * 100 : 0,
    };
  });

  if (!data.length) {
    return <EmptyChart message="No Pareto data available" />;
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 16, right: 8, bottom: 60, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis dataKey="sku" tick={{ fill: c.axis, fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
          <YAxis yAxisId="left" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis yAxisId="right" orientation="right" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${c.grid}`, background: "var(--surface)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }} />
          <Legend />
          <Bar yAxisId="left" dataKey="revenue" fill={c.primary} name="Revenue ($k)" />
          <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke={c.danger} strokeWidth={3} dot={false} name="Cumulative %" />
          <ReferenceLine yAxisId="right" y={80} stroke={c.danger} strokeDasharray="5 5" />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Seasonality Analysis Chart
export function SeasonalityChart() {
  const state = useDashboardState();
  const c = chartColors();
  const monthlySales = state.result?.analytics_snapshot?.monthly_sales ?? [];
  const data = monthlySales.slice(-12).map((item, index, entries) => {
    const current = Number(item.total_quantity_sold ?? 0);
    const previous = index > 0 ? Number(entries[index - 1].total_quantity_sold ?? current) : current;
    const seasonal =
      entries
        .slice(0, index + 1)
        .reduce((sum, entry) => sum + Number(entry.total_quantity_sold ?? 0), 0) /
      (index + 1);

    return {
      month: String(item.month ?? `M${index + 1}`).slice(5) || String(item.month ?? `M${index + 1}`),
      current,
      previous,
      seasonal: Math.round(seasonal),
    };
  });

  if (!data.length) {
    return <EmptyChart message="No seasonality data available" />;
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis dataKey="month" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${c.grid}`, background: "var(--surface)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }} />
          <Legend />
          <Area type="monotone" dataKey="seasonal" stroke={c.quaternary} fill={c.fillQuaternary} strokeWidth={2} name="Seasonal Avg" />
          <Area type="monotone" dataKey="current" stroke={c.primary} fill={c.fillPrimary} strokeWidth={2} name="Current Year" />
          <Area type="monotone" dataKey="previous" stroke={c.secondary} fill={c.fillSecondary} strokeWidth={2} name="Previous Year" />
        </AreaChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// Anomaly Detection Chart
export function AnomalyDetectionChart() {
  const state = useDashboardState();
  const c = chartColors();
  
  const data = state.result?.analytics_snapshot?.demand_anomalies?.slice(0, 30).map((item, index) => {
    const anomaly = item as NonNullable<AnalyticsSnapshot["demand_anomalies"]>[number] & {
      actual_demand?: number;
      expected_demand?: number;
      is_anomaly?: boolean;
      quantity_sold?: number;
      type?: string;
    };
    const actual = anomaly.actual_demand ?? anomaly.quantity_sold ?? 0;

    return {
      date: String(anomaly.date || `Day ${index + 1}`),
      actual,
      expected: anomaly.expected_demand ?? actual,
      anomaly: anomaly.is_anomaly ?? Boolean(anomaly.type),
    };
  }) ?? [];

  if (!data.length) {
    return <EmptyChart message="No anomaly data available" />;
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.grid} />
          <XAxis dataKey="date" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${c.grid}`, background: "var(--surface)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }} />
          <Legend />
          <Line type="monotone" dataKey="expected" stroke={c.secondary} strokeWidth={2} dot={false} name="Ожидаемое" />
          <Line type="monotone" dataKey="actual" stroke={c.primary} strokeWidth={2} dot={false} name="Факт" />
          <Scatter dataKey="anomaly" fill={c.danger}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.anomaly ? c.danger : "transparent"} />
            ))}
          </Scatter>
        </ComposedChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

// KPI Trend Cards
export function KPITrendCards() {
  const state = useDashboardState();
  const c = chartColors();
  
  const kpis = [
    { 
      title: "Общая выручка", 
      value: formatCompactMoney(state.result?.summary_metrics.total_revenue || 0), 
      note: "Текущий анализ", 
      color: c.primary 
    },
    { 
      title: "Оборачиваемость", 
      value: (state.result?.summary_metrics.inventory_turnover_ratio || 0).toFixed(2), 
      note: "Текущий запуск", 
      color: c.secondary 
    },
    { 
      title: "Риск дефицита", 
      value: formatPercent(
        ((state.result?.recommendations?.filter(r => (r.stockout_risk ?? 0) > 0.5).length || 0) / Math.max(1, state.result?.recommendations?.length || 0)) * 100, 
        0
      ), 
      note: "По рекомендациям", 
      color: c.danger 
    },
    { 
      title: "Надёжность прогноза", 
      value: formatPercent(state.summary.medianConfidence, 0), 
      note: "Текущий анализ", 
      color: c.success 
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, index) => (
        <div key={index} className="relative overflow-hidden rounded-xl border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
          <div className="absolute inset-0 bg-gradient-to-br from-transparent to-[color:var(--surface-muted)]" />
          <div className="relative space-y-2">
            <p className="text-xs font-medium text-[color:var(--muted)] uppercase">{kpi.title}</p>
            <p className="text-2xl font-bold">{kpi.value}</p>
            <p className="text-xs font-medium text-[color:var(--muted)]">{kpi.note}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// Empty Chart Component
function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-80 items-center justify-center rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)]">
      <div className="text-center">
        <p className="text-sm text-[color:var(--muted)]">{message}</p>
        <p className="mt-1 text-xs text-[color:var(--muted)]">Загрузите файл, чтобы увидеть аналитику</p>
      </div>
    </div>
  );
}
