from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.domain.constants import DEFAULT_SERVICE_LEVEL, PRIORITY_ORDER

DEFAULT_SAFETY_STOCK_PERCENT = 0.2
DEFAULT_SUPPLY_LEAD_TIME_DAYS = 3


def build_purchase_recommendations_df(
    product_forecast: pd.DataFrame,
    safety_stock_percent: float = DEFAULT_SAFETY_STOCK_PERCENT,
    supply_lead_time_days: int = DEFAULT_SUPPLY_LEAD_TIME_DAYS,
    service_level: float = DEFAULT_SERVICE_LEVEL,
) -> pd.DataFrame:
    recommendations: list[dict[str, Any]] = []

    if product_forecast.empty:
        return pd.DataFrame(recommendations)

    z_score = _service_level_to_zscore(service_level)

    for row in product_forecast.itertuples(index=False):
        average_daily_demand = float(row.average_daily_demand)
        horizon_days = int(row.horizon_days)
        current_stock = float(row.current_stock)
        predicted_quantity = float(row.predicted_quantity)
        lower_bound = float(getattr(row, "lower_bound", 0.0))
        upper_bound = float(getattr(row, "upper_bound", predicted_quantity))
        forecast_model = getattr(row, "forecast_model", "baseline")
        confidence_score = float(getattr(row, "confidence_score", 50.0))
        demand_pattern = getattr(row, "demand_pattern", "stable")

        forecast_std = max((upper_bound - lower_bound) / max(2 * z_score, 1), average_daily_demand * 0.25)
        lead_time_demand = average_daily_demand * supply_lead_time_days
        safety_stock = max(
            predicted_quantity * safety_stock_percent,
            z_score * forecast_std * math.sqrt(max(supply_lead_time_days, 1)),
        )
        reorder_point = lead_time_demand + safety_stock
        target_stock_level = max(predicted_quantity + safety_stock + lead_time_demand, reorder_point)
        recommended_order_qty = max(0.0, target_stock_level - current_stock)
        inventory_gap = target_stock_level - current_stock
        days_of_cover = _calculate_days_of_cover(current_stock, average_daily_demand)
        stockout_risk = _calculate_stockout_risk(
            current_stock=current_stock,
            lead_time_demand=lead_time_demand,
            demand_std=forecast_std,
            lead_time_days=supply_lead_time_days,
        )
        overstock_risk = _calculate_overstock_risk(
            current_stock=current_stock,
            lower_bound=lower_bound,
            predicted_quantity=predicted_quantity,
            horizon_days=horizon_days,
            average_daily_demand=average_daily_demand,
        )

        priority = _define_priority(
            recommended_order_qty=recommended_order_qty,
            days_of_cover=days_of_cover,
            stockout_risk=stockout_risk,
            overstock_risk=overstock_risk,
            supply_lead_time_days=supply_lead_time_days,
        )
        recommendation_type = _define_recommendation_type(priority, recommended_order_qty)
        explanation = _build_explanation(
            product_name=row.product_name,
            priority=priority,
            days_of_cover=days_of_cover,
            stockout_risk=stockout_risk,
            overstock_risk=overstock_risk,
            recommended_order_qty=recommended_order_qty,
            reorder_point=reorder_point,
            target_stock_level=target_stock_level,
            forecast_model=forecast_model,
            confidence_score=confidence_score,
            demand_pattern=demand_pattern,
        )

        recommendations.append(
            {
                "sku": row.sku,
                "product_name": row.product_name,
                "category": row.category,
                "type": recommendation_type,
                "action_group": _map_action_group(recommendation_type),
                "priority": priority,
                "current_stock": round(current_stock, 2),
                "stock_days_left": round(days_of_cover, 1) if math.isfinite(days_of_cover) else "Нет продаж",
                "days_of_cover": round(days_of_cover, 1) if math.isfinite(days_of_cover) else None,
                "average_daily_demand": round(average_daily_demand, 2),
                "predicted_quantity": round(predicted_quantity, 2),
                "recommended_order_qty": int(round(recommended_order_qty)),
                "expected_revenue": round(float(row.expected_revenue), 2),
                "safety_stock": round(safety_stock, 2),
                "lead_time_demand": round(lead_time_demand, 2),
                "reorder_point": round(reorder_point, 2),
                "target_stock_level": round(target_stock_level, 2),
                "inventory_gap": round(inventory_gap, 2),
                "service_level": service_level,
                "stockout_risk": round(stockout_risk, 3),
                "stockout_risk_label": _risk_label(stockout_risk),
                "overstock_risk": round(overstock_risk, 3),
                "overstock_risk_label": _risk_label(overstock_risk),
                "forecast_model": forecast_model,
                "confidence_score": round(confidence_score, 1),
                "confidence_label": getattr(row, "confidence_label", "medium"),
                "demand_pattern": demand_pattern,
                "qty_if_lead_time_plus_2": int(
                    round(
                        max(
                            0.0,
                            target_stock_level + average_daily_demand * 2 - current_stock,
                        )
                    )
                ),
                "qty_if_safety_stock_plus_10pct": int(
                    round(
                        max(
                            0.0,
                            predicted_quantity
                            + safety_stock * 1.1
                            + lead_time_demand
                            - current_stock,
                        )
                    )
                ),
                "qty_if_demand_growth_10pct": int(
                    round(max(0.0, target_stock_level * 1.1 - current_stock))
                ),
                "message": explanation,
                "explanation": explanation,
            }
        )

    recommendations_df = pd.DataFrame(recommendations)
    if recommendations_df.empty:
        return recommendations_df

    recommendations_df["priority_rank"] = recommendations_df["priority"].map(PRIORITY_ORDER)
    recommendations_df = recommendations_df.sort_values(
        ["priority_rank", "stockout_risk", "expected_revenue"],
        ascending=[True, False, False],
    ).drop(columns=["priority_rank"])

    return recommendations_df.reset_index(drop=True)


def build_category_recommendations(
    recommendations: pd.DataFrame,
) -> list[dict[str, Any]]:
    if recommendations.empty:
        return []

    grouped = (
        recommendations.groupby("category", as_index=False)
        .agg(
            skus=("sku", "nunique"),
            urgent_skus=("priority", lambda values: int(pd.Series(values).isin(["critical", "high"]).sum())),
            total_recommended_order_qty=("recommended_order_qty", "sum"),
            forecast_revenue=("expected_revenue", "sum"),
            average_stockout_risk=("stockout_risk", "mean"),
            average_overstock_risk=("overstock_risk", "mean"),
        )
        .sort_values(["urgent_skus", "forecast_revenue"], ascending=[False, False])
    )

    rows: list[dict[str, Any]] = []
    for row in grouped.itertuples(index=False):
        action = "monitor"
        if row.urgent_skus > 0:
            action = "urgent"
        elif row.total_recommended_order_qty > 0:
            action = "planned"
        elif row.average_overstock_risk >= 0.55:
            action = "no_action"

        rows.append(
            {
                "category": row.category,
                "skus": int(row.skus),
                "urgent_skus": int(row.urgent_skus),
                "total_recommended_order_qty": int(round(float(row.total_recommended_order_qty))),
                "forecast_revenue": round(float(row.forecast_revenue), 2),
                "average_stockout_risk": round(float(row.average_stockout_risk), 3),
                "average_overstock_risk": round(float(row.average_overstock_risk), 3),
                "action_group": action,
                "message": _build_category_message(
                    category=row.category,
                    action=action,
                    urgent_skus=int(row.urgent_skus),
                    total_recommended_order_qty=float(row.total_recommended_order_qty),
                ),
            }
        )

    return rows


def build_executive_insights(
    product_sales: pd.DataFrame,
    product_forecast: pd.DataFrame,
    recommendations: pd.DataFrame,
    category_recommendations: list[dict[str, Any]],
) -> list[str]:
    insights: list[str] = []

    if product_sales.empty:
        return ["Недостаточно данных для формирования управленческих выводов."]

    top_product = product_sales.sort_values("total_revenue", ascending=False).iloc[0]
    insights.append(
        f"Главный драйвер выручки сейчас — {top_product['product_name']}: "
        f"{round(float(top_product['total_revenue']), 2)} выручки."
    )

    if not recommendations.empty:
        urgent_skus = int(recommendations["priority"].isin(["critical", "high"]).sum())
        total_order = int(round(float(recommendations["recommended_order_qty"].sum())))
        high_risk = recommendations.sort_values("stockout_risk", ascending=False).iloc[0]
        insights.append(
            f"В зоне повышенного риска дефицита {urgent_skus} SKU; "
            f"суммарно стоит рассмотреть закупку около {total_order} ед."
        )
        insights.append(
            f"Самый чувствительный SKU — {high_risk['product_name']}: "
            f"покрытие {high_risk['stock_days_left']} дн., "
            f"риск дефицита {round(float(high_risk['stockout_risk']) * 100, 1)}%."
        )

        if "overstock_risk" in recommendations.columns:
            frozen_items = recommendations[recommendations["overstock_risk"] >= 0.6]
            if not frozen_items.empty:
                insights.append(
                    f"Есть риск заморозки денег в запасах по {len(frozen_items)} SKU. "
                    "Их лучше перевести в режим monitor/no action."
                )

    if category_recommendations:
        hottest_category = category_recommendations[0]
        insights.append(
            f"Наиболее приоритетная категория — {hottest_category['category']}: "
            f"{hottest_category['urgent_skus']} срочных SKU."
        )

    if not product_forecast.empty:
        projected_revenue = float(product_forecast["expected_revenue"].sum())
        median_confidence = float(product_forecast["confidence_score"].median())
        insights.append(
            f"Прогнозируемая выручка на горизонт — {round(projected_revenue, 2)}, "
            f"медианная надёжность прогноза {round(median_confidence, 1)}/100."
        )

    return insights[:6]


def _calculate_days_of_cover(current_stock: float, average_daily_demand: float) -> float:
    if average_daily_demand <= 0:
        return float("inf")
    return current_stock / average_daily_demand


def _calculate_stockout_risk(
    current_stock: float,
    lead_time_demand: float,
    demand_std: float,
    lead_time_days: int,
) -> float:
    sigma = max(demand_std * math.sqrt(max(lead_time_days, 1)), 1.0)
    z_value = (current_stock - lead_time_demand) / sigma
    return max(0.0, min(1.0, 1 - _normal_cdf(z_value)))


def _calculate_overstock_risk(
    current_stock: float,
    lower_bound: float,
    predicted_quantity: float,
    horizon_days: int,
    average_daily_demand: float,
) -> float:
    buffer_demand = max(predicted_quantity - lower_bound, average_daily_demand * max(horizon_days / 4, 1))
    if buffer_demand <= 0:
        return 0.0
    excess_ratio = max(0.0, current_stock - predicted_quantity) / buffer_demand
    return max(0.0, min(1.0, excess_ratio / 2))


def _define_priority(
    recommended_order_qty: float,
    days_of_cover: float,
    stockout_risk: float,
    overstock_risk: float,
    supply_lead_time_days: int,
) -> str:
    if recommended_order_qty <= 0 and overstock_risk < 0.45:
        return "info"
    if days_of_cover <= max(1, supply_lead_time_days) or stockout_risk >= 0.75:
        return "critical"
    if days_of_cover <= supply_lead_time_days + 3 or stockout_risk >= 0.55:
        return "high"
    if recommended_order_qty > 0 or stockout_risk >= 0.35:
        return "medium"
    if overstock_risk >= 0.55:
        return "low"
    return "low"


def _define_recommendation_type(priority: str, recommended_order_qty: float) -> str:
    if recommended_order_qty <= 0:
        return "no_purchase_needed"
    if priority == "critical":
        return "urgent_purchase"
    if priority == "high":
        return "planned_purchase"
    if priority == "medium":
        return "monitor_and_purchase"
    return "optional_purchase"


def _map_action_group(recommendation_type: str) -> str:
    return {
        "urgent_purchase": "urgent",
        "planned_purchase": "planned",
        "monitor_and_purchase": "monitor",
        "optional_purchase": "monitor",
        "no_purchase_needed": "no_action",
    }.get(recommendation_type, "monitor")


def _build_explanation(
    product_name: str,
    priority: str,
    days_of_cover: float,
    stockout_risk: float,
    overstock_risk: float,
    recommended_order_qty: float,
    reorder_point: float,
    target_stock_level: float,
    forecast_model: str,
    confidence_score: float,
    demand_pattern: str,
) -> str:
    cover_text = "нет стабильных продаж" if not math.isfinite(days_of_cover) else f"{round(days_of_cover, 1)} дн."

    if recommended_order_qty <= 0:
        return (
            f"По товару «{product_name}» активная закупка не требуется. "
            f"Покрытие: {cover_text}, риск излишка {round(overstock_risk * 100, 1)}%."
        )

    return (
        f"{priority.capitalize()} приоритет для «{product_name}»: покрытие {cover_text}, "
        f"риск дефицита {round(stockout_risk * 100, 1)}%, "
        f"точка заказа {round(reorder_point, 1)} ед., целевой запас {round(target_stock_level, 1)} ед. "
        f"Рекомендуемый заказ: {int(round(recommended_order_qty))} ед. "
        f"Модель прогноза: {forecast_model}, надёжность {round(confidence_score, 1)}/100, "
        f"паттерн спроса: {demand_pattern}."
    )


def _build_category_message(
    category: str,
    action: str,
    urgent_skus: int,
    total_recommended_order_qty: float,
) -> str:
    if action == "urgent":
        return (
            f"Категория {category} требует быстрого внимания: {urgent_skus} SKU в риске дефицита, "
            f"ориентир закупки {int(round(total_recommended_order_qty))} ед."
        )
    if action == "planned":
        return (
            f"По категории {category} стоит запланировать закупку "
            f"примерно на {int(round(total_recommended_order_qty))} ед."
        )
    if action == "no_action":
        return f"Категорию {category} лучше держать под наблюдением без активной дозакупки."
    return f"Категория {category} требует мониторинга спроса и остатка."


def _risk_label(risk: float) -> str:
    if risk >= 0.75:
        return "high"
    if risk >= 0.45:
        return "medium"
    return "low"


def _service_level_to_zscore(service_level: float) -> float:
    if service_level >= 0.98:
        return 2.05
    if service_level >= 0.95:
        return 1.64
    if service_level >= 0.9:
        return 1.28
    return 1.0


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))
