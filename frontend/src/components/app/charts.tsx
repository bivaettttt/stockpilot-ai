"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipValueType,
} from "recharts";
import { ChartShell } from "@/src/components/app/chart-shell";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";

type ChartName = string | number;

function chartColors() {
  return {
    grid: "var(--border)",
    axis: "var(--muted)",
    line: "var(--accent)",
    lineSecondary: "#10b981",
    lineTertiary: "#f59e0b",
    fill: "color-mix(in srgb, var(--accent) 20%, transparent)",
    fillSecondary: "color-mix(in srgb, #10b981 20%, transparent)",
    fillTertiary: "color-mix(in srgb, #f59e0b 20%, transparent)",
    risk: "#ef4444",
    success: "#10b981",
    warning: "#f59e0b",
  };
}

export function DemandTrendChart() {
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
    state.result?.daily_sales?.slice(-30).map((point) => ({
      date: point.date.slice(5),
      demand: point.quantity_sold,
      revenue: point.revenue / 1000,
      forecast: null as number | null,
    })) ?? [];
  const forecastData = Object.entries(forecastByDate).map(([date, forecast]) => ({
    date: date.slice(5),
    demand: null as number | null,
    revenue: null as number | null,
    forecast,
  }));
  const data = [...historicalData, ...forecastData];

  if (!data.length) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg bg-[color:var(--surface-muted)]">
        <div className="text-center">
          <p className="text-sm text-[color:var(--muted)]">Нет данных</p>
          <p className="text-xs text-[color:var(--muted)] mt-1">Загрузите файл, чтобы увидеть динамику</p>
        </div>
      </div>
    );
  }

  return (
    <ChartShell className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fill: c.axis, fontSize: 11 }} 
            axisLine={false} 
            tickLine={false}
          />
          <YAxis 
            tick={{ fill: c.axis, fontSize: 11 }} 
            axisLine={false} 
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: `1px solid ${c.grid}`,
              background: "var(--surface)",
              color: "var(--text)",
              boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            }}
            formatter={(value: TooltipValueType | undefined, name: ChartName | undefined) => {
              if (typeof value !== 'number') return ["", ""];
              if (name === "revenue") return [`${value.toFixed(1)} тыс.`, "Выручка"];
              if (name === "forecast") return [value.toFixed(0), "Прогноз"];
              return [value.toFixed(0), "Спрос"];
            }}
          />
          <Area 
            type="monotone" 
            dataKey="forecast" 
            stroke={c.lineSecondary} 
            fill={c.fillSecondary} 
            strokeWidth={1.5}
            strokeDasharray="5 5"
          />
          <Area 
            type="monotone" 
            dataKey="demand" 
            stroke={c.line} 
            fill={c.fill} 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function ForecastConfidenceChart() {
  const state = useDashboardState();
  const c = chartColors();
  const data =
    state.result?.product_forecast?.slice(0, 20).map((item) => {
      const confidence = item.confidence_score ?? 0;
      let riskLevel = "low";
      let riskColor = c.success;
      
      if (confidence < 55) {
        riskLevel = "high";
        riskColor = c.risk;
      } else if (confidence < 75) {
        riskLevel = "medium";
        riskColor = c.warning;
      }

      return {
        sku: item.sku,
        confidence,
        riskLevel,
        riskColor,
      };
    }) ?? [];

  if (!data.length) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg bg-[color:var(--surface-muted)]">
        <div className="text-center">
          <p className="text-sm text-[color:var(--muted)]">Нет данных по прогнозу</p>
          <p className="text-xs text-[color:var(--muted)] mt-1">Запустите анализ, чтобы увидеть надёжность по SKU</p>
        </div>
      </div>
    );
  }

  return (
    <ChartShell className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
          <XAxis 
            dataKey="sku" 
            tick={{ fill: c.axis, fontSize: 10 }} 
            axisLine={false} 
            tickLine={false}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            tick={{ fill: c.axis, fontSize: 11 }} 
            axisLine={false} 
            tickLine={false}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: `1px solid ${c.grid}`,
              background: "var(--surface)",
              color: "var(--text)",
              boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            }}
            formatter={(value: TooltipValueType | undefined, name: ChartName | undefined) => {
              if (name === "confidence" && typeof value === 'number') {
                const item = data.find(d => d.confidence === value);
                return [
                  <div key="confidence">
                    <div style={{ color: item?.riskColor }}>
                      {value.toFixed(1)}%
                    </div>
                    <div className="text-xs text-[color:var(--muted)]">
                      Риск: {item?.riskLevel === "high" ? "высокий" : item?.riskLevel === "medium" ? "средний" : "низкий"}
                    </div>
                  </div>,
                  "Надёжность"
                ];
              }
              return [value, name];
            }}
          />
          <Line 
            type="monotone" 
            dataKey="confidence" 
            stroke={c.line} 
            strokeWidth={2}
            dot={(props: { cx?: number; cy?: number; payload?: { riskColor: string } }) => {
              const { cx, cy, payload } = props;
              return (
                <circle 
                  cx={cx} 
                  cy={cy} 
                  r={4} 
                  fill={payload?.riskColor}
                  stroke="var(--surface)"
                  strokeWidth={2}
                />
              );
            }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-4 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-[color:var(--success)]" />
          <span className="text-[color:var(--muted)]">Low Risk (&gt;75%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-[color:var(--warning)]" />
          <span className="text-[color:var(--muted)]">Medium Risk (55-75%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-[color:var(--risk)]" />
          <span className="text-[color:var(--muted)]">High Risk (&lt;55%)</span>
        </div>
      </div>
    </ChartShell>
  );
}
