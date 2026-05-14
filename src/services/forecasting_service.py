from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_FORECAST_HORIZON_DAYS = 14
DEFAULT_SEASON_LENGTH = 7
CONFIDENCE_Z_SCORE = 1.64


@dataclass(frozen=True)
class ModelSelectionResult:
    model_name: str
    forecasts: np.ndarray
    score: float
    mae: float
    wape: float
    bias: float
    residual_std: float


ForecastModel = Callable[[np.ndarray, int], np.ndarray]


def build_product_forecast_df(
    df: pd.DataFrame,
    horizon_days: int = DEFAULT_FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    forecasts: list[dict[str, Any]] = []

    for sku, product_df in df.groupby("sku"):
        product_df = product_df.copy().sort_values("date")
        daily_demand = get_daily_demand_series(product_df)
        series = daily_demand.to_numpy(dtype=float)

        selection = _select_best_model(series=series, horizon_days=horizon_days)
        predicted_daily = selection.forecasts
        predicted_quantity = float(predicted_daily.sum())

        demand_std = float(np.std(series, ddof=0)) if len(series) > 0 else 0.0
        uncertainty = max(
            selection.residual_std,
            demand_std * 0.35,
        ) * math.sqrt(max(horizon_days, 1))

        lower_bound = max(0.0, predicted_quantity - CONFIDENCE_Z_SCORE * uncertainty)
        upper_bound = max(predicted_quantity, predicted_quantity + CONFIDENCE_Z_SCORE * uncertainty)

        confidence_score = _build_confidence_score(
            score=selection.score,
            observation_count=len(series),
            intermittency_ratio=_intermittency_ratio(series),
        )

        product_name = product_df["product_name"].iloc[-1]
        category = product_df["category"].iloc[-1]
        current_stock = float(product_df["stock_on_hand"].iloc[-1])
        average_daily_demand = float(series.mean()) if len(series) > 0 else 0.0
        trend_percent = _trend_percent(series)
        seasonality_strength = _seasonality_strength(series)
        demand_pattern = _classify_demand_pattern(series, trend_percent)

        expected_revenue = _calculate_expected_revenue(
            product_df=product_df,
            predicted_quantity=predicted_quantity,
        )

        forecasts.append(
            {
                "sku": sku,
                "product_name": product_name,
                "category": category,
                "horizon_days": horizon_days,
                "current_stock": round(current_stock, 2),
                "average_daily_demand": round(average_daily_demand, 2),
                "predicted_quantity": round(predicted_quantity, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "expected_revenue": round(expected_revenue, 2),
                "forecast_model": selection.model_name,
                "forecast_score": round(selection.score, 4),
                "confidence_score": round(confidence_score, 1),
                "confidence_label": _confidence_label(confidence_score),
                "trend_percent": round(trend_percent, 1),
                "seasonality_strength": round(seasonality_strength, 3),
                "demand_pattern": demand_pattern,
                "intermittency_ratio": round(_intermittency_ratio(series), 3),
            }
        )

    forecast_df = pd.DataFrame(forecasts)
    if forecast_df.empty:
        return forecast_df

    return forecast_df.sort_values(
        ["predicted_quantity", "expected_revenue"],
        ascending=[False, False],
    ).reset_index(drop=True)


def build_daily_forecast_chart_df(
    df: pd.DataFrame,
    horizon_days: int = DEFAULT_FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    chart_rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame(chart_rows)

    max_date = pd.to_datetime(df["date"], errors="coerce").max()

    for sku, product_df in df.groupby("sku"):
        product_df = product_df.copy().sort_values("date")
        series = get_daily_demand_series(product_df).to_numpy(dtype=float)
        selection = _select_best_model(series=series, horizon_days=horizon_days)

        for day_number, prediction in enumerate(selection.forecasts, start=1):
            chart_rows.append(
                {
                    "date": max_date + pd.Timedelta(days=day_number),
                    "sku": sku,
                    "product_name": product_df["product_name"].iloc[-1],
                    "predicted_quantity": round(float(prediction), 2),
                    "forecast_model": selection.model_name,
                }
            )

    return pd.DataFrame(chart_rows)


def get_daily_demand_series(product_df: pd.DataFrame) -> pd.Series:
    prepared_df = product_df.copy()
    prepared_df["date"] = pd.to_datetime(prepared_df["date"], errors="coerce")
    prepared_df = prepared_df.dropna(subset=["date"])

    if prepared_df.empty:
        return pd.Series(dtype=float)

    daily_demand = prepared_df.groupby("date")["quantity_sold"].sum().sort_index()
    if daily_demand.empty:
        return pd.Series(dtype=float)

    full_date_range = pd.date_range(daily_demand.index.min(), daily_demand.index.max(), freq="D")
    return daily_demand.reindex(full_date_range, fill_value=0)


def _select_best_model(series: np.ndarray, horizon_days: int) -> ModelSelectionResult:
    cleaned_series = np.clip(np.nan_to_num(series, nan=0.0), a_min=0.0, a_max=None)
    if len(cleaned_series) == 0:
        return ModelSelectionResult(
            model_name="no_history_fallback",
            forecasts=np.zeros(horizon_days),
            score=0.0,
            mae=0.0,
            wape=0.0,
            bias=0.0,
            residual_std=0.0,
        )

    if len(cleaned_series) < 4:
        fallback_forecast = _moving_average_model(cleaned_series, horizon_days)
        return ModelSelectionResult(
            model_name="short_history_fallback",
            forecasts=fallback_forecast,
            score=0.0,
            mae=0.0,
            wape=0.0,
            bias=0.0,
            residual_std=float(np.std(cleaned_series, ddof=0)),
        )

    backtest_horizon = min(max(3, min(horizon_days, 14)), max(1, len(cleaned_series) // 4))
    train = cleaned_series[:-backtest_horizon]
    test = cleaned_series[-backtest_horizon:]

    if len(train) == 0:
        train = cleaned_series
        test = cleaned_series[-1:]
        backtest_horizon = len(test)

    candidates = _candidate_models(cleaned_series)
    results: list[ModelSelectionResult] = []

    for model_name, model in candidates.items():
        predictions = np.clip(model(train, backtest_horizon), a_min=0.0, a_max=None)
        residuals = test - predictions[: len(test)]
        mae = float(np.mean(np.abs(residuals))) if len(residuals) > 0 else 0.0
        denominator = float(np.abs(test).sum())
        wape = float(np.abs(residuals).sum() / denominator) if denominator > 0 else mae
        rmse = float(np.sqrt(np.mean(np.square(residuals)))) if len(residuals) > 0 else 0.0
        normalized_rmse = rmse / max(float(np.mean(test)), 1.0)
        bias = float(predictions.sum() - test.sum()) / max(float(test.sum()), 1.0)
        score = 0.5 * wape + 0.3 * normalized_rmse + 0.2 * abs(bias)
        results.append(
            ModelSelectionResult(
                model_name=model_name,
                forecasts=np.clip(model(cleaned_series, horizon_days), a_min=0.0, a_max=None),
                score=float(score),
                mae=mae,
                wape=float(wape),
                bias=float(bias),
                residual_std=float(np.std(residuals, ddof=0)) if len(residuals) > 0 else 0.0,
            )
        )

    return min(results, key=lambda item: item.score)


def select_best_model(series: np.ndarray, horizon_days: int) -> ModelSelectionResult:
    return _select_best_model(series=series, horizon_days=horizon_days)


def _candidate_models(series: np.ndarray) -> dict[str, ForecastModel]:
    intermittency = _intermittency_ratio(series)
    candidates: dict[str, ForecastModel] = {
        "naive_last_day": _naive_last_model,
        "moving_average_7": _moving_average_model,
        "exp_smoothing": _exp_smoothing_model,
    }

    if len(series) >= 14:
        candidates["seasonal_weekly"] = _seasonal_weekly_model

    if intermittency >= 0.35:
        candidates["croston_intermittent"] = _croston_model

    return candidates


def _naive_last_model(train: np.ndarray, horizon: int) -> np.ndarray:
    last_value = float(train[-1]) if len(train) > 0 else 0.0
    return np.full(horizon, last_value)


def _moving_average_model(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) == 0:
        return np.zeros(horizon)
    window = min(7, len(train))
    average = float(np.mean(train[-window:]))
    return np.full(horizon, average)


def _exp_smoothing_model(train: np.ndarray, horizon: int, alpha: float = 0.35) -> np.ndarray:
    if len(train) == 0:
        return np.zeros(horizon)

    level = float(train[0])
    for value in train[1:]:
        level = alpha * float(value) + (1 - alpha) * level

    return np.full(horizon, max(level, 0.0))


def _seasonal_weekly_model(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) < DEFAULT_SEASON_LENGTH:
        return _moving_average_model(train, horizon)

    base_pattern = train[-DEFAULT_SEASON_LENGTH :]
    if len(train) >= DEFAULT_SEASON_LENGTH * 2:
        previous_pattern = train[-DEFAULT_SEASON_LENGTH * 2 : -DEFAULT_SEASON_LENGTH]
        base_pattern = (base_pattern + previous_pattern) / 2

    return np.array([float(base_pattern[index % len(base_pattern)]) for index in range(horizon)])


def _croston_model(train: np.ndarray, horizon: int, alpha: float = 0.2) -> np.ndarray:
    non_zero_positions = np.flatnonzero(train > 0)
    if len(non_zero_positions) == 0:
        return np.zeros(horizon)

    demand_estimate = float(train[non_zero_positions[0]])
    interval_estimate = float(non_zero_positions[0] + 1)
    interval = 1

    for value in train[1:]:
        if value > 0:
            demand_estimate = alpha * float(value) + (1 - alpha) * demand_estimate
            interval_estimate = alpha * interval + (1 - alpha) * interval_estimate
            interval = 1
        else:
            interval += 1

    forecast = demand_estimate / max(interval_estimate, 1.0)
    return np.full(horizon, max(forecast, 0.0))


def _calculate_expected_revenue(product_df: pd.DataFrame, predicted_quantity: float) -> float:
    if "selling_price" in product_df.columns:
        selling_price = pd.to_numeric(product_df["selling_price"], errors="coerce").dropna()
        if not selling_price.empty:
            return float(predicted_quantity * float(selling_price.iloc[-1]))

    total_revenue = float(product_df["revenue"].sum())
    total_quantity = float(product_df["quantity_sold"].sum())
    if total_quantity <= 0:
        return 0.0

    return float(predicted_quantity * (total_revenue / total_quantity))


def _build_confidence_score(
    score: float,
    observation_count: int,
    intermittency_ratio: float,
) -> float:
    base = 100 - min(score * 100, 85)
    observation_factor = min(observation_count / 45, 1.0)
    intermittency_penalty = intermittency_ratio * 25
    return max(5.0, min(99.0, base * (0.55 + 0.45 * observation_factor) - intermittency_penalty))


def _confidence_label(confidence_score: float) -> str:
    if confidence_score >= 78:
        return "high"
    if confidence_score >= 55:
        return "medium"
    return "low"


def _trend_percent(series: np.ndarray) -> float:
    if len(series) < 7:
        return 0.0

    window = min(28, len(series))
    y = series[-window:]
    x = np.arange(window, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    baseline = max(intercept + slope * (window / 2), 1.0)
    trend = float((slope * 7 / baseline) * 100)
    if math.isnan(trend) or math.isinf(trend):
        return 0.0
    return trend


def _seasonality_strength(series: np.ndarray) -> float:
    if len(series) < 14:
        return 0.0

    weekday_values = [series[index::DEFAULT_SEASON_LENGTH].mean() for index in range(DEFAULT_SEASON_LENGTH)]
    overall_mean = max(float(np.mean(series)), 1.0)
    strength = float(np.std(weekday_values) / overall_mean)
    if math.isnan(strength) or math.isinf(strength):
        return 0.0
    return strength


def _intermittency_ratio(series: np.ndarray) -> float:
    if len(series) == 0:
        return 0.0
    return float(np.mean(series == 0))


def _classify_demand_pattern(series: np.ndarray, trend_percent: float) -> str:
    intermittency = _intermittency_ratio(series)
    mean = float(np.mean(series)) if len(series) > 0 else 0.0
    std = float(np.std(series, ddof=0)) if len(series) > 0 else 0.0
    coefficient = std / mean if mean > 0 else 0.0

    if intermittency >= 0.45:
        return "intermittent"
    if trend_percent >= 8:
        return "growing"
    if trend_percent <= -8:
        return "declining"
    if coefficient >= 1.0:
        return "volatile"
    return "stable"
