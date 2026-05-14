from __future__ import annotations

from typing import Any


def build_abc_analysis(top_products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Строит ABC-анализ по товарам на основе выручки.

    Группы:
    - A: товары, которые формируют примерно первые 80% выручки;
    - B: товары, которые доводят накопленную долю до 95%;
    - C: остальные товары.
    """
    if not top_products:
        return []

    prepared_products = []

    for product in top_products:
        revenue = _to_float(product.get("total_revenue", 0))

        prepared_products.append(
            {
                "sku": product.get("sku", ""),
                "product_name": product.get("product_name", ""),
                "category": product.get("category", "Без категории"),
                "total_revenue": revenue,
                "total_quantity_sold": _to_float(product.get("total_quantity_sold", 0)),
            }
        )

    prepared_products = sorted(
        prepared_products,
        key=lambda item: item["total_revenue"],
        reverse=True,
    )

    total_revenue = sum(item["total_revenue"] for item in prepared_products)

    if total_revenue <= 0:
        return [
            {
                **item,
                "revenue_share_percent": 0,
                "cumulative_share_percent": 0,
                "abc_class": "C",
                "abc_description": "Товар без значимого вклада в выручку.",
            }
            for item in prepared_products
        ]

    cumulative_revenue = 0.0
    result = []

    for item in prepared_products:
        cumulative_revenue += item["total_revenue"]

        revenue_share_percent = item["total_revenue"] / total_revenue * 100
        cumulative_share_percent = cumulative_revenue / total_revenue * 100

        abc_class = _get_abc_class(cumulative_share_percent)

        result.append(
            {
                **item,
                "revenue_share_percent": round(revenue_share_percent, 2),
                "cumulative_share_percent": round(cumulative_share_percent, 2),
                "abc_class": abc_class,
                "abc_description": _get_abc_description(abc_class),
            }
        )

    return result


def build_abc_summary(
    abc_analysis: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Строит краткую сводку по ABC-группам.
    """
    summary = {
        "A": {"products_count": 0, "total_revenue": 0.0},
        "B": {"products_count": 0, "total_revenue": 0.0},
        "C": {"products_count": 0, "total_revenue": 0.0},
    }

    for item in abc_analysis:
        abc_class = item.get("abc_class", "C")

        if abc_class not in summary:
            abc_class = "C"

        summary[abc_class]["products_count"] += 1
        summary[abc_class]["total_revenue"] += _to_float(item.get("total_revenue", 0))

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


def _get_abc_class(cumulative_share_percent: float) -> str:
    if cumulative_share_percent <= 80:
        return "A"

    if cumulative_share_percent <= 95:
        return "B"

    return "C"


def _get_abc_description(abc_class: str) -> str:
    descriptions = {
        "A": "Ключевой товар. Требует постоянного контроля наличия.",
        "B": "Средний вклад. Нужно контролировать, но не в первую очередь.",
        "C": "Низкий вклад. Можно закупать осторожнее.",
    }

    return descriptions.get(abc_class, descriptions["C"])


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0

        return float(value)
    except (TypeError, ValueError):
        return 0.0
