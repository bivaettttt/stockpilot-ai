import type { AnalyzeResponse } from "@/src/types/api";

export function extractForecastingSnapshot(result: AnalyzeResponse | null) {
  return {
    productForecast: result?.product_forecast ?? [],
    dailyForecast: result?.daily_forecast_chart_data ?? [],
    confidenceMedian:
      result?.product_forecast.length
        ? result.product_forecast
            .map((item) => item.confidence_score ?? 0)
            .sort((a, b) => a - b)[Math.floor(result.product_forecast.length / 2)] ?? 0
        : 0,
  };
}
