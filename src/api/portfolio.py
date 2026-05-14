from __future__ import annotations

from typing import Any


def build_abc_xyz_matrix(
    abc_analysis: list[dict[str, Any]],
    xyz_analysis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Строит совмещённую ABC/XYZ-матрицу по SKU.

    ABC отвечает за вклад товара в выручку.
    XYZ отвечает за стабильность спроса.

    Комбинация даёт управленческую интерпретацию:
    - AX: ключевой товар со стабильным спросом;
    - AZ: ключевой товар, но спрос хаотичный;
    - CZ: слабый и нестабильный товар.
    """
    if not abc_analysis or not xyz_analysis:
        return []

    xyz_by_sku = {str(item.get("sku", "")): item for item in xyz_analysis}

    matrix = []

    for abc_item in abc_analysis:
        sku = str(abc_item.get("sku", ""))
        xyz_item = xyz_by_sku.get(sku)

        if not xyz_item:
            continue

        abc_class = str(abc_item.get("abc_class", "C"))
        xyz_class = str(xyz_item.get("xyz_class", "Z"))
        combined_class = f"{abc_class}{xyz_class}"

        matrix.append(
            {
                "sku": sku,
                "product_name": abc_item.get("product_name", ""),
                "category": abc_item.get("category", "Без категории"),
                "abc_class": abc_class,
                "xyz_class": xyz_class,
                "abc_xyz_class": combined_class,
                "total_revenue": _to_float(abc_item.get("total_revenue", 0)),
                "total_quantity_sold": _to_float(abc_item.get("total_quantity_sold", 0)),
                "revenue_share_percent": _to_float(abc_item.get("revenue_share_percent", 0)),
                "cumulative_share_percent": _to_float(abc_item.get("cumulative_share_percent", 0)),
                "average_daily_demand": _to_float(xyz_item.get("average_daily_demand", 0)),
                "coefficient_of_variation": _to_float(xyz_item.get("coefficient_of_variation", 0)),
                "management_action": _get_management_action(combined_class),
                "management_priority": _get_management_priority(combined_class),
            }
        )

    return sorted(
        matrix,
        key=lambda item: (
            _priority_sort_value(item["management_priority"]),
            -item["total_revenue"],
        ),
    )


def build_abc_xyz_summary(
    matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Строит сводку по ABC/XYZ-комбинациям.
    """
    classes = [
        "AX",
        "AY",
        "AZ",
        "BX",
        "BY",
        "BZ",
        "CX",
        "CY",
        "CZ",
    ]

    summary = {
        class_name: {
            "products_count": 0,
            "total_revenue": 0.0,
            "revenue_share_percent": 0.0,
            "management_action": _get_management_action(class_name),
            "management_priority": _get_management_priority(class_name),
        }
        for class_name in classes
    }

    for item in matrix:
        class_name = str(item.get("abc_xyz_class", "CZ"))

        if class_name not in summary:
            class_name = "CZ"

        summary[class_name]["products_count"] += 1
        summary[class_name]["total_revenue"] += _to_float(item.get("total_revenue", 0))

    total_revenue = sum(group["total_revenue"] for group in summary.values())

    for group in summary.values():
        if total_revenue > 0:
            group["revenue_share_percent"] = round(
                group["total_revenue"] / total_revenue * 100,
                2,
            )

        group["total_revenue"] = round(group["total_revenue"], 2)

    return summary


def _get_management_action(combined_class: str) -> str:
    actions = {
        "AX": "Держать в наличии всегда. Максимальный контроль остатков.",
        "AY": "Ключевой товар. Контролировать часто, учитывать колебания спроса.",
        "AZ": "Денежный, но нестабильный товар. Закупать осторожно, небольшими партиями.",
        "BX": "Хороший стабильный товар. Поддерживать регулярный запас.",
        "BY": "Средний товар. Контролировать по стандартному циклу закупок.",
        "BZ": "Средний вклад и нестабильный спрос. Не завышать остатки.",
        "CX": "Стабильный, но слабый по выручке товар. Держать минимальный запас.",
        "CY": "Низкий вклад. Закупать только при подтверждённом спросе.",
        "CZ": "Слабый и нестабильный товар. Кандидат на сокращение или вывод.",
    }

    return actions.get(combined_class, actions["CZ"])


def _get_management_priority(combined_class: str) -> str:
    high_priority = {"AX", "AY", "AZ"}
    medium_priority = {"BX", "BY", "BZ", "CX"}

    if combined_class in high_priority:
        return "high"

    if combined_class in medium_priority:
        return "medium"

    return "low"


def _priority_sort_value(priority: str) -> int:
    values = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    return values.get(priority, 3)


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0

        return float(value)
    except (TypeError, ValueError):
        return 0.0
