from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.services.forecasting_service import get_daily_demand_series, select_best_model

MIN_HISTORY_DAYS = 8
MAX_BACKTEST_DAYS = 14


def build_analysis_reliability(
    prepared_df: pd.DataFrame,
    product_forecast: pd.DataFrame,
    data_quality: dict[str, Any],
    *,
    horizon_days: int,
) -> dict[str, Any]:
    sku_reliability: list[dict[str, Any]] = []
    weighted_abs_error_sum = 0.0
    actual_volume_sum = 0.0
    mae_values: list[float] = []
    bias_values: list[float] = []
    valid_sku_count = 0
    backtest_periods: list[int] = []

    overall_warnings: list[dict[str, Any]] = []
    stockout_warning = _build_stockout_warning(prepared_df)
    if stockout_warning:
        overall_warnings.append(stockout_warning)

    promo_warning = _build_promo_warning(prepared_df)
    if promo_warning:
        overall_warnings.append(promo_warning)

    forecast_lookup = {}
    if not product_forecast.empty and "sku" in product_forecast.columns:
        forecast_lookup = {
            str(row["sku"]): row
            for _, row in product_forecast.iterrows()
        }

    for sku, product_df in prepared_df.groupby("sku"):
        product_df = product_df.copy().sort_values("date")
        daily_series = get_daily_demand_series(product_df)
        metrics = _build_sku_reliability_metrics(
            sku=str(sku),
            product_df=product_df,
            daily_series=daily_series,
            horizon_days=horizon_days,
            forecast_row=forecast_lookup.get(str(sku)),
        )
        sku_reliability.append(metrics)

        if metrics["wape"] is not None:
            valid_sku_count += 1
            mae_values.append(float(metrics["mae"]))
            bias_values.append(float(metrics["bias"]))
            weighted_abs_error_sum += float(metrics["_absolute_error_sum"])
            actual_volume_sum += float(metrics["_actual_sum"])
            backtest_periods.append(int(metrics["_backtest_period_days"]))

    low_confidence_skus = [item for item in sku_reliability if item["confidence"] == "low"]
    insufficient_skus = [item for item in sku_reliability if item["confidence"] == "insufficient_data"]

    overall_wape = (
        round(weighted_abs_error_sum / actual_volume_sum, 3)
        if actual_volume_sum > 0
        else None
    )
    overall_mae = round(float(np.mean(mae_values)), 3) if mae_values else None
    overall_bias = round(float(np.mean(bias_values)), 3) if bias_values else None
    reliability_score = _build_reliability_score(
        wape=overall_wape,
        bias=overall_bias,
        coverage_ratio=(valid_sku_count / len(sku_reliability)) if sku_reliability else 0.0,
    )
    overall_confidence = _confidence_label_from_metrics(
        wape=overall_wape,
        bias=overall_bias,
        coverage_ratio=(valid_sku_count / len(sku_reliability)) if sku_reliability else 0.0,
    )

    if insufficient_skus:
        overall_warnings.append(
            _warning(
                code="insufficient_history_for_backtest",
                title="Не для всех SKU хватает истории",
                message=(
                    f"Для {len(insufficient_skus)} SKU нельзя честно оценить прогноз по истории. "
                    "По ним надёжность показана как insufficient_data."
                ),
                suggestion="Соберите более длинную историю продаж перед интерпретацией прогноза.",
            )
        )

    if low_confidence_skus:
        overall_warnings.append(
            _warning(
                code="low_reliability_skus",
                title="Есть SKU с низкой надёжностью прогноза",
                message=(
                    f"Низкая надёжность обнаружена у {len(low_confidence_skus)} SKU. "
                    "Их стоит проверить вручную перед закупкой."
                ),
                suggestion="Откройте вкладку надёжности анализа и проверьте причины по этим SKU.",
            )
        )

    return {
        "data_quality": {
            "score": _build_data_quality_score(data_quality),
            "label": _build_data_quality_label(data_quality),
            "warnings": [
                _warning(
                    code="data_quality_issue",
                    title="Есть предупреждения по качеству данных",
                    message=f"В анализе есть {data_quality.get('warnings_count', 0)} предупреждений и {data_quality.get('errors_count', 0)} ошибок качества данных.",
                    suggestion="Проверьте предупреждения по данным перед интерпретацией прогноза.",
                )
            ]
            if (data_quality.get("warnings_count", 0) or data_quality.get("errors_count", 0))
            else [],
        },
        "forecast_quality": {
            "overall_confidence": overall_confidence,
            "reliability_score": reliability_score,
            "wape": overall_wape,
            "mae": overall_mae,
            "bias": overall_bias,
            "backtest_period_days": int(round(np.mean(backtest_periods))) if backtest_periods else None,
            "coverage": round(valid_sku_count / len(sku_reliability), 3) if sku_reliability else None,
            "warnings": overall_warnings,
        },
        "sku_reliability": [
            {
                key: value
                for key, value in item.items()
                if not key.startswith("_")
            }
            for item in sorted(
                sku_reliability,
                key=lambda row: (
                    _confidence_rank(row["confidence"]),
                    row["wape"] if row["wape"] is not None else 999.0,
                    row["sku"],
                ),
            )
        ],
        "warnings": overall_warnings,
    }


def _build_sku_reliability_metrics(
    *,
    sku: str,
    product_df: pd.DataFrame,
    daily_series: pd.Series,
    horizon_days: int,
    forecast_row: pd.Series | None,
) -> dict[str, Any]:
    product_name = str(product_df["product_name"].iloc[-1])
    category = str(product_df["category"].iloc[-1])
    demand_pattern = (
        str(forecast_row["demand_pattern"])
        if forecast_row is not None and "demand_pattern" in forecast_row
        else None
    )
    data_points = int(len(product_df))
    history_days = int(len(daily_series))
    zero_sales_days = int((daily_series <= 0).sum())
    stockout_risk_days = int(
        ((pd.to_numeric(product_df["stock_on_hand"], errors="coerce").fillna(0) <= 0) &
         (pd.to_numeric(product_df["quantity_sold"], errors="coerce").fillna(0) <= 0)).sum()
    )
    promo_share = _promo_share(product_df)

    holdout_days = min(MAX_BACKTEST_DAYS, max(3, history_days // 4))
    if history_days < MIN_HISTORY_DAYS or history_days <= holdout_days:
        return {
            "sku": sku,
            "product_name": product_name,
            "category": category,
            "demand_pattern": demand_pattern,
            "data_points": data_points,
            "history_days": history_days,
            "zero_sales_days": zero_sales_days,
            "stockout_risk_days": stockout_risk_days,
            "wape": None,
            "mae": None,
            "bias": None,
            "confidence": "insufficient_data",
            "reliability_reason": "Недостаточно истории",
            "reason": "Недостаточно истории",
            "_absolute_error_sum": 0.0,
            "_actual_sum": 0.0,
            "_backtest_period_days": 0,
        }

    train = daily_series.iloc[:-holdout_days].to_numpy(dtype=float)
    actual = daily_series.iloc[-holdout_days:].to_numpy(dtype=float)

    if len(train) < 4 or len(actual) == 0:
        return {
            "sku": sku,
            "product_name": product_name,
            "category": category,
            "demand_pattern": demand_pattern,
            "data_points": data_points,
            "history_days": history_days,
            "zero_sales_days": zero_sales_days,
            "stockout_risk_days": stockout_risk_days,
            "wape": None,
            "mae": None,
            "bias": None,
            "confidence": "insufficient_data",
            "reliability_reason": "Прогноз основан на короткой истории",
            "reason": "Прогноз основан на короткой истории",
            "_absolute_error_sum": 0.0,
            "_actual_sum": 0.0,
            "_backtest_period_days": 0,
        }

    selection = select_best_model(train, holdout_days)
    predicted = selection.forecasts[:holdout_days]
    absolute_errors = np.abs(actual - predicted)
    mae = float(np.mean(absolute_errors)) if len(actual) > 0 else None
    actual_sum = float(np.abs(actual).sum())
    wape = float(absolute_errors.sum() / actual_sum) if actual_sum > 0 else None
    bias = float(predicted.sum() - actual.sum()) / max(float(actual.sum()), 1.0) if actual_sum > 0 else None

    confidence = _confidence_label_for_sku(
        wape=wape,
        bias=bias,
        zero_sales_share=(zero_sales_days / history_days) if history_days > 0 else 0.0,
        stockout_risk_days=stockout_risk_days,
        promo_share=promo_share,
        demand_pattern=demand_pattern,
    )
    reliability_reason = _build_reliability_reason(
        confidence=confidence,
        history_days=history_days,
        zero_sales_days=zero_sales_days,
        stockout_risk_days=stockout_risk_days,
        promo_share=promo_share,
        demand_pattern=demand_pattern,
    )

    return {
        "sku": sku,
        "product_name": product_name,
        "category": category,
        "demand_pattern": demand_pattern,
        "data_points": data_points,
        "history_days": history_days,
        "zero_sales_days": zero_sales_days,
        "stockout_risk_days": stockout_risk_days,
        "wape": round(wape, 3) if wape is not None else None,
        "mae": round(mae, 3) if mae is not None else None,
        "bias": round(bias, 3) if bias is not None else None,
        "confidence": confidence,
        "reliability_reason": reliability_reason,
        "reason": reliability_reason,
        "_absolute_error_sum": float(absolute_errors.sum()),
        "_actual_sum": actual_sum,
        "_backtest_period_days": holdout_days,
    }


def _build_data_quality_score(data_quality: dict[str, Any]) -> int | None:
    metrics = [
        data_quality.get("completeness_score"),
        data_quality.get("validity_score"),
        data_quality.get("consistency_score"),
    ]
    numeric_metrics = [float(value) for value in metrics if value is not None]
    if not numeric_metrics:
        return None
    return int(round(sum(numeric_metrics) / len(numeric_metrics)))


def _build_data_quality_label(data_quality: dict[str, Any]) -> str:
    score = _build_data_quality_score(data_quality)
    if score is None:
        return "insufficient_data"
    if score >= 85:
        return "good"
    if score >= 65:
        return "medium"
    return "low"


def _build_reliability_score(*, wape: float | None, bias: float | None, coverage_ratio: float) -> int | None:
    if wape is None or bias is None:
        return None
    score = 100
    score -= min(wape, 1.0) * 60
    score -= min(abs(bias), 1.0) * 25
    score -= (1 - min(max(coverage_ratio, 0.0), 1.0)) * 15
    return int(round(max(0.0, min(score, 100.0))))


def _confidence_label_from_metrics(*, wape: float | None, bias: float | None, coverage_ratio: float) -> str:
    if wape is None or bias is None or coverage_ratio < 0.35:
        return "insufficient_data"
    if wape <= 0.15 and abs(bias) <= 0.08 and coverage_ratio >= 0.7:
        return "high"
    if wape <= 0.28 and abs(bias) <= 0.18 and coverage_ratio >= 0.5:
        return "medium"
    return "low"


def _confidence_label_for_sku(
    *,
    wape: float | None,
    bias: float | None,
    zero_sales_share: float,
    stockout_risk_days: int,
    promo_share: float | None,
    demand_pattern: str | None,
) -> str:
    if wape is None or bias is None:
        return "insufficient_data"
    if stockout_risk_days > 0 or zero_sales_share >= 0.45:
        return "low"
    if promo_share is not None and promo_share >= 0.35:
        return "low"
    if demand_pattern in {"volatile", "intermittent"} and wape > 0.18:
        return "low"
    if wape <= 0.15 and abs(bias) <= 0.08:
        return "high"
    if wape <= 0.28 and abs(bias) <= 0.18:
        return "medium"
    return "low"


def _build_reliability_reason(
    *,
    confidence: str,
    history_days: int,
    zero_sales_days: int,
    stockout_risk_days: int,
    promo_share: float | None,
    demand_pattern: str | None,
) -> str:
    if confidence == "insufficient_data":
        return "Недостаточно истории"
    if stockout_risk_days > 0:
        return "Возможны stockout-периоды"
    if promo_share is not None and promo_share >= 0.35:
        return "Промо-периоды могут искажать спрос"
    if zero_sales_days / max(history_days, 1) >= 0.4:
        return "Много нулевых продаж"
    if demand_pattern in {"volatile", "intermittent"}:
        return "Нестабильный спрос"
    if history_days < 21:
        return "Прогноз основан на короткой истории"
    return "Спрос выглядит стабильным"


def _build_stockout_warning(prepared_df: pd.DataFrame) -> dict[str, Any] | None:
    if prepared_df.empty:
        return None
    stock_series = pd.to_numeric(prepared_df["stock_on_hand"], errors="coerce").fillna(0)
    sold_series = pd.to_numeric(prepared_df["quantity_sold"], errors="coerce").fillna(0)
    mask = (stock_series <= 0) & (sold_series <= 0)
    if not mask.any():
        return None

    return _warning(
        code="possible_stockout_censored_demand",
        title="Возможное искажение спроса из-за нулевых остатков",
        message=(
            "В некоторые дни товар отсутствовал на складе. Продажи в эти дни могли быть нулевыми не из-за отсутствия спроса, "
            "а из-за отсутствия товара."
        ),
        suggestion="Проверьте такие SKU перед принятием закупочных решений.",
    )


def _build_promo_warning(prepared_df: pd.DataFrame) -> dict[str, Any] | None:
    if prepared_df.empty or "promotion_flag" not in prepared_df.columns:
        return None

    promo_series = _coerce_boolean(prepared_df["promotion_flag"])
    promo_share = float(promo_series.mean()) if len(promo_series) > 0 else 0.0
    if promo_share < 0.25:
        return None

    return _warning(
        code="promotion_periods_can_distort_forecast",
        title="Промо-периоды могут искажать прогноз",
        message=(
            "В данных много промо-дней. Повышенные продажи в такие периоды могут влиять на прогноз "
            "и делать его менее стабильным."
        ),
        suggestion="Сравните SKU с промо-периодами отдельно перед интерпретацией прогноза.",
    )


def _promo_share(product_df: pd.DataFrame) -> float | None:
    if "promotion_flag" not in product_df.columns:
        return None
    promo_series = _coerce_boolean(product_df["promotion_flag"])
    return float(promo_series.mean()) if len(promo_series) > 0 else None


def _coerce_boolean(series: pd.Series) -> pd.Series:
    normalized = (
        series.fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
    )
    return normalized.isin({"1", "true", "yes", "y", "да", "promo", "акция"})


def _warning(*, code: str, title: str, message: str, suggestion: str | None) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "message": message,
        "suggestion": suggestion,
    }


def _confidence_rank(value: str) -> int:
    order = {
        "low": 0,
        "insufficient_data": 1,
        "medium": 2,
        "high": 3,
    }
    return order.get(value, 4)
