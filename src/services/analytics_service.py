from __future__ import annotations

from typing import Any

import pandas as pd


def build_analytics_snapshot(
    df: pd.DataFrame,
    product_sales: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> dict[str, list[dict[str, Any]]]:
    return {
        "weekday_sales": _weekday_sales(df),
        "monthly_sales": _monthly_sales(df),
        "supplier_sales": _supplier_sales(df),
        "promotion_performance": _promotion_performance(df),
        "inventory_health": _inventory_health(product_sales, recommendations),
        "demand_anomalies": _demand_anomalies(df),
    }


def _weekday_sales(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    weekday_df = df.copy()
    weekday_df["weekday"] = weekday_df["date"].dt.day_name()
    weekday_df["weekday_number"] = weekday_df["date"].dt.dayofweek

    result = (
        weekday_df.groupby(["weekday_number", "weekday"], as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity_sold=("quantity_sold", "sum"),
            average_order_value=("revenue", "mean"),
        )
        .sort_values("weekday_number")
        .drop(columns=["weekday_number"])
    )

    return result.round(2).to_dict(orient="records")


def _monthly_sales(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    monthly_df = df.copy()
    monthly_df["month"] = monthly_df["date"].dt.to_period("M").astype(str)

    result = (
        monthly_df.groupby("month", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity_sold=("quantity_sold", "sum"),
            unique_products=("sku", "nunique"),
        )
        .sort_values("month")
    )

    return result.round(2).to_dict(orient="records")


def _supplier_sales(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "supplier" not in df.columns:
        return []

    supplier_df = df[df["supplier"].fillna("").astype(str).str.strip() != ""]
    if supplier_df.empty:
        return []

    result = (
        supplier_df.groupby("supplier", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity_sold=("quantity_sold", "sum"),
            unique_products=("sku", "nunique"),
        )
        .sort_values("total_revenue", ascending=False)
        .head(10)
    )

    return result.round(2).to_dict(orient="records")


def _promotion_performance(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "promotion_flag" not in df.columns:
        return []

    promo_df = df.copy()
    promo_df["promotion_segment"] = promo_df["promotion_flag"].map(
        {True: "Промо", False: "Без промо"}
    )

    result = (
        promo_df.groupby("promotion_segment", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_quantity_sold=("quantity_sold", "sum"),
            average_revenue=("revenue", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    return result.round(2).to_dict(orient="records")


def _inventory_health(
    product_sales: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> list[dict[str, Any]]:
    if product_sales.empty:
        return []

    urgent_count = 0
    excess_count = 0
    recommended_units = 0.0
    revenue_at_risk = 0.0

    if not recommendations.empty:
        urgent_count = int(
            recommendations["priority"].isin(["critical", "high"]).sum()
        )
        overstock_risk = (
            recommendations["overstock_risk"]
            if "overstock_risk" in recommendations.columns
            else pd.Series([0] * len(recommendations))
        )
        excess_count = int((overstock_risk > 0.55).sum())
        recommended_units = float(recommendations["recommended_order_qty"].sum())
        revenue_at_risk = float(recommendations["expected_revenue"].sum())

    return [
        {
            "metric": "urgent_skus",
            "value": urgent_count,
            "label": "SKU с риском дефицита",
        },
        {
            "metric": "excess_skus",
            "value": excess_count,
            "label": "SKU с риском излишка",
        },
        {
            "metric": "recommended_units",
            "value": round(recommended_units, 2),
            "label": "Рекомендуемый объём закупки",
        },
        {
            "metric": "forecast_revenue",
            "value": round(revenue_at_risk, 2),
            "label": "Прогнозируемая выручка по SKU",
        },
    ]


def _demand_anomalies(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    anomaly_rows: list[dict[str, Any]] = []

    for sku, product_df in df.groupby("sku"):
        daily = (
            product_df.groupby("date", as_index=False)
            .agg(quantity_sold=("quantity_sold", "sum"))
            .sort_values("date")
        )
        if len(daily) < 10:
            continue

        rolling_mean = daily["quantity_sold"].rolling(window=7, min_periods=4).mean()
        rolling_std = daily["quantity_sold"].rolling(window=7, min_periods=4).std().fillna(0)

        daily["upper"] = rolling_mean + 2 * rolling_std
        daily["lower"] = (rolling_mean - 2 * rolling_std).clip(lower=0)

        latest_rows = daily.tail(14)
        spike_rows = latest_rows[latest_rows["quantity_sold"] > latest_rows["upper"]]
        drop_rows = latest_rows[latest_rows["quantity_sold"] < latest_rows["lower"]]

        for row in spike_rows.itertuples():
            anomaly_rows.append(
                {
                    "sku": sku,
                    "product_name": product_df["product_name"].iloc[-1],
                    "date": row.date.strftime("%Y-%m-%d"),
                    "type": "spike",
                    "quantity_sold": round(float(row.quantity_sold), 2),
                }
            )

        for row in drop_rows.itertuples():
            anomaly_rows.append(
                {
                    "sku": sku,
                    "product_name": product_df["product_name"].iloc[-1],
                    "date": row.date.strftime("%Y-%m-%d"),
                    "type": "drop",
                    "quantity_sold": round(float(row.quantity_sold), 2),
                }
            )

    return anomaly_rows[:20]
