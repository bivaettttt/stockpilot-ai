from __future__ import annotations

from typing import Any

import pandas as pd

X_THRESHOLD = 30
Y_THRESHOLD = 70


def build_xyz_analysis(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Строит XYZ-анализ по стабильности спроса.

    Логика:
    - считаем дневные продажи по каждому товару;
    - считаем среднее дневное потребление;
    - считаем стандартное отклонение;
    - считаем коэффициент вариации;
    - присваиваем класс X/Y/Z.

    Классы для малого бизнеса:
    - X: стабильный спрос, коэффициент вариации до 30%;
    - Y: умеренно нестабильный спрос, коэффициент вариации до 70%;
    - Z: хаотичный спрос, коэффициент вариации выше 70%.

    Почему пороги не 10% и 25%:
    у малого бизнеса дневные продажи часто низкие и волатильные,
    поэтому классические строгие пороги почти все товары отправляют в Z.
    """
    if df.empty:
        return []

    required_columns = {
        "date",
        "sku",
        "product_name",
        "category",
        "quantity_sold",
        "revenue",
    }

    if not required_columns.issubset(set(df.columns)):
        return []

    working_df = df.copy()
    working_df["date"] = pd.to_datetime(working_df["date"], errors="coerce")
    working_df["quantity_sold"] = pd.to_numeric(
        working_df["quantity_sold"],
        errors="coerce",
    ).fillna(0)
    working_df["revenue"] = pd.to_numeric(
        working_df["revenue"],
        errors="coerce",
    ).fillna(0)

    working_df = working_df.dropna(subset=["date"])

    if working_df.empty:
        return []

    daily_demand = (
        working_df.groupby(
            ["sku", "product_name", "category", "date"],
            as_index=False,
        )
        .agg(
            quantity_sold=("quantity_sold", "sum"),
            revenue=("revenue", "sum"),
        )
        .sort_values(["sku", "date"])
    )

    grouped = (
        daily_demand.groupby(["sku", "product_name", "category"], as_index=False)
        .agg(
            observation_days=("date", "nunique"),
            total_quantity_sold=("quantity_sold", "sum"),
            total_revenue=("revenue", "sum"),
            average_daily_demand=("quantity_sold", "mean"),
            demand_std=("quantity_sold", "std"),
        )
        .fillna({"demand_std": 0})
    )

    result = []

    for _, row in grouped.iterrows():
        average_daily_demand = _to_float(row["average_daily_demand"])
        demand_std = _to_float(row["demand_std"])

        if average_daily_demand <= 0:
            coefficient_of_variation = 0.0
            xyz_class = "Z"
        else:
            coefficient_of_variation = demand_std / average_daily_demand * 100
            xyz_class = _get_xyz_class(coefficient_of_variation)

        result.append(
            {
                "sku": str(row["sku"]),
                "product_name": str(row["product_name"]),
                "category": str(row["category"]),
                "observation_days": int(row["observation_days"]),
                "total_quantity_sold": round(
                    _to_float(row["total_quantity_sold"]),
                    2,
                ),
                "total_revenue": round(_to_float(row["total_revenue"]), 2),
                "average_daily_demand": round(average_daily_demand, 2),
                "demand_std": round(demand_std, 2),
                "coefficient_of_variation": round(coefficient_of_variation, 2),
                "xyz_class": xyz_class,
                "xyz_description": _get_xyz_description(xyz_class),
            }
        )

    return sorted(
        result,
        key=lambda item: (
            item["xyz_class"],
            -item["total_revenue"],
        ),
    )


def build_xyz_summary(
    xyz_analysis: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Строит краткую сводку по XYZ-группам.
    """
    summary = {
        "X": {"products_count": 0, "total_revenue": 0.0},
        "Y": {"products_count": 0, "total_revenue": 0.0},
        "Z": {"products_count": 0, "total_revenue": 0.0},
    }

    for item in xyz_analysis:
        xyz_class = item.get("xyz_class", "Z")

        if xyz_class not in summary:
            xyz_class = "Z"

        summary[xyz_class]["products_count"] += 1
        summary[xyz_class]["total_revenue"] += _to_float(item.get("total_revenue", 0))

    total_revenue = sum(group["total_revenue"] for group in summary.values())

    for group in summary.values():
        if total_revenue > 0:
            group["revenue_share_percent"] = round(
                group["total_revenue"] / total_revenue * 100,
                2,
            )
        else:
            group["revenue_share_percent"] = 0

        group["total_revenue"] = round(group["total_revenue"], 2)

    return summary


def _get_xyz_class(coefficient_of_variation: float) -> str:
    if coefficient_of_variation <= X_THRESHOLD:
        return "X"

    if coefficient_of_variation <= Y_THRESHOLD:
        return "Y"

    return "Z"


def _get_xyz_description(xyz_class: str) -> str:
    descriptions = {
        "X": "Стабильный спрос. Товар хорошо подходит для плановой закупки.",
        "Y": "Умеренно нестабильный спрос. Нужен регулярный контроль запасов.",
        "Z": "Хаотичный спрос. Закупать осторожно, прогноз менее надёжен.",
    }

    return descriptions.get(xyz_class, descriptions["Z"])


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0

        return float(value)
    except (TypeError, ValueError):
        return 0.0
