import pandas as pd

from src.services.recommendation_service import (
    DEFAULT_SAFETY_STOCK_PERCENT,
    DEFAULT_SUPPLY_LEAD_TIME_DAYS,
    build_category_recommendations,
    build_executive_insights,
    build_purchase_recommendations_df,
)


def build_purchase_recommendations(
    product_forecast: pd.DataFrame,
    safety_stock_percent: float = DEFAULT_SAFETY_STOCK_PERCENT,
    supply_lead_time_days: int = DEFAULT_SUPPLY_LEAD_TIME_DAYS,
) -> pd.DataFrame:
    return build_purchase_recommendations_df(
        product_forecast=product_forecast,
        safety_stock_percent=safety_stock_percent,
        supply_lead_time_days=supply_lead_time_days,
    )


def build_business_insights(
    product_sales: pd.DataFrame,
    product_forecast: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> list[str]:
    category_recommendations = build_category_recommendations(recommendations)
    return build_executive_insights(
        product_sales=product_sales,
        product_forecast=product_forecast,
        recommendations=recommendations,
        category_recommendations=category_recommendations,
    )


def _calculate_stock_days_left(
    current_stock: float,
    average_daily_demand: float,
) -> float:
    if average_daily_demand <= 0:
        return float("inf")

    return current_stock / average_daily_demand


def _define_priority(
    stock_days_left: float,
    recommended_order_qty: float,
) -> str:
    if recommended_order_qty <= 0:
        return "info"

    if stock_days_left <= 3:
        return "critical"

    if stock_days_left <= 7:
        return "high"

    if stock_days_left <= 14:
        return "medium"

    return "low"


def _define_recommendation_type(
    stock_days_left: float,
    recommended_order_qty: float,
) -> str:
    if recommended_order_qty <= 0:
        return "no_purchase_needed"

    if stock_days_left <= 3:
        return "urgent_purchase"

    if stock_days_left <= 7:
        return "planned_purchase"

    if stock_days_left <= 14:
        return "monitor_and_purchase"

    return "optional_purchase"


def _build_message(
    product_name: str,
    horizon_days: int,
    current_stock: float,
    average_daily_demand: float,
    predicted_quantity: float,
    recommended_order_qty: float,
    stock_days_left: float,
    priority: str,
    recommendation_type: str,
) -> str:
    rounded_order_qty = int(round(recommended_order_qty))
    rounded_stock = round(current_stock, 2)
    rounded_daily_demand = round(average_daily_demand, 2)
    rounded_predicted_quantity = round(predicted_quantity, 2)

    if stock_days_left == float("inf"):
        return (
            f"По товару «{product_name}» нет продаж в анализируемом периоде. "
            f"Новая закупка не рекомендуется до появления устойчивого спроса."
        )

    rounded_stock_days_left = round(stock_days_left, 1)

    if recommendation_type == "urgent_purchase":
        return (
            f"Срочно закупите около {rounded_order_qty} ед. товара «{product_name}». "
            f"Текущий остаток: {rounded_stock} ед., его хватит примерно на "
            f"{rounded_stock_days_left} дн. Средний спрос: "
            f"{rounded_daily_demand} ед./день."
        )

    if recommendation_type == "planned_purchase":
        return (
            f"Запланируйте закупку около {rounded_order_qty} ед. товара "
            f"«{product_name}». Остатка хватит примерно на "
            f"{rounded_stock_days_left} дн., прогноз спроса на {horizon_days} дн.: "
            f"{rounded_predicted_quantity} ед."
        )

    if recommendation_type == "monitor_and_purchase":
        return (
            f"Следите за товаром «{product_name}» и рассмотрите закупку "
            f"около {rounded_order_qty} ед. Остатка хватит примерно на "
            f"{rounded_stock_days_left} дн."
        )

    if recommendation_type == "optional_purchase":
        return (
            f"Закупка товара «{product_name}» не критична, но можно заказать "
            f"около {rounded_order_qty} ед. для поддержания запаса на период "
            f"{horizon_days} дн."
        )

    return (
        f"По товару «{product_name}» новая закупка сейчас не требуется. "
        f"Остаток: {rounded_stock} ед., прогноз спроса на {horizon_days} дн.: "
        f"{rounded_predicted_quantity} ед."
    )
