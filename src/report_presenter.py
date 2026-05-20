from __future__ import annotations

from typing import Any

import pandas as pd

VALUE_LABELS = {
    "critical": "Критический",
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
    "info": "Информация",
    "stable": "стабильный",
    "growing": "растущий",
    "declining": "снижающийся",
    "volatile": "нестабильный",
    "monitor": "наблюдать",
    "no_action": "действие не требуется",
    "purchase": "закупить",
    "review": "проверить вручную",
    "exp_smoothing": "экспоненциальное сглаживание",
    "moving_average_7": "скользящее среднее 7 дней",
    "seasonal_weekly": "недельная сезонность",
    "naive_last_day": "последний день как ориентир",
    "short_history_fallback": "короткая история продаж",
    "insufficient_data": "недостаточно данных",
    "new": "Новая",
    "accepted": "Принято",
    "in_purchase": "В закупке",
    "rejected": "Отклонено",
    "done": "Выполнено",
    "urgent_purchase": "Срочная закупка",
    "planned_purchase": "Плановая закупка",
    "monitor_and_purchase": "Наблюдать и закупить при необходимости",
    "optional_purchase": "Необязательная закупка",
    "no_purchase_needed": "Закупка не требуется",
    "high_stockout_risk": "Высокий риск дефицита",
    "medium_stockout_risk": "Средний риск дефицита",
    "low_stockout_risk": "Низкий риск дефицита",
    "high_overstock_risk": "Высокий риск излишка",
    "medium_overstock_risk": "Средний риск излишка",
    "low_overstock_risk": "Низкий риск излишка",
    "high_confidence": "Высокая надёжность",
    "medium_confidence": "Средняя надёжность",
    "low_confidence": "Низкая надёжность",
    "high_priority": "Высокий приоритет",
    "medium_priority": "Средний приоритет",
    "low_priority": "Низкий приоритет",
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
    "x": "Стабильный",
    "y": "Умеренно нестабильный",
    "z": "Хаотичный",
}


BUSINESS_PURCHASE_PLAN_COLUMNS = [
    "SKU",
    "Товар",
    "Категория",
    "Поставщик",
    "Приоритет",
    "Остаток",
    "Дней покрытия",
    "Риск дефицита",
    "Рекомендовано системой",
    "С учётом поставщика",
    "Итоговое количество",
    "Причина",
    "Статус",
    "Комментарий",
]


ABC_XYZ_BUSINESS_COLUMNS = [
    "SKU",
    "Товар",
    "Категория",
    "ABC",
    "XYZ",
    "Класс ABC/XYZ",
    "Приоритет",
    "Выручка",
    "Продано, ед.",
    "Доля выручки, %",
    "Накопленная доля, %",
    "Средний спрос в день",
    "Вариативность спроса, %",
    "Действие",
]


def localize_value(value: Any) -> Any:
    if value is None:
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return stripped
        label = VALUE_LABELS.get(stripped.lower())
        return label if label is not None else stripped

    return value


def localize_forecast_confidence(value: Any) -> str:
    """Return a grammatically correct Russian label for forecast confidence."""
    if value is None:
        return "нет данных"

    raw = str(value).strip().lower()
    labels = {
        "high": "высокая",
        "medium": "средняя",
        "low": "низкая",
        "insufficient_data": "недостаточно данных",
        "высокий": "высокая",
        "средний": "средняя",
        "низкий": "низкая",
        "высокая": "высокая",
        "средняя": "средняя",
        "низкая": "низкая",
    }
    if raw in labels:
        return labels[raw]

    localized = localize_value(value)
    localized_raw = str(localized).strip().lower()
    return labels.get(localized_raw, localized_raw or "нет данных")


def localize_series(series: pd.Series) -> pd.Series:
    return series.map(localize_value)


def shorten_text(value: Any, limit: int = 110) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    text = text.replace("\n", " ").replace("  ", " ")
    first_sentence = text.split(". ")[0].strip()
    if first_sentence:
        text = first_sentence
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def to_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def format_money_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    return f"{number:,.0f} ₽".replace(",", " ")


def format_percent_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    if abs(number) <= 1:
        number *= 100
    formatted = f"{number:,.1f}".replace(",", " ").replace(".", ",")
    return f"{formatted}%"


def format_quantity_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    return f"{number:,.0f} ед.".replace(",", " ")


def format_days_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    formatted = f"{number:,.1f}".replace(",", " ").replace(".", ",")
    return f"{formatted} дн."


def format_score_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    return f"{number:,.0f}/100".replace(",", " ")


def format_integer_text(value: Any) -> str:
    number = to_number(value)
    if number is None:
        return "Нет данных"
    return f"{number:,.0f}".replace(",", " ")


def build_business_reason(row: pd.Series) -> str:
    coverage = format_days_text(row.get("stock_days_left")).replace(" дн.", "")
    risk = format_percent_text(row.get("stockout_risk"))
    qty_value = (
        row.get("final_order_qty")
        if row.get("final_order_qty") not in (None, "")
        else row.get("adjusted_order_qty")
        if row.get("adjusted_order_qty") not in (None, "")
        else row.get("recommended_order_qty")
    )
    qty_number = to_number(qty_value) or 0

    if qty_number > 0:
        lead = "Требуется пополнение запаса" if (to_number(row.get("stockout_risk")) or 0) >= 0.6 else "Стоит пополнить запас"
        return f"{lead}: запаса хватит примерно на {coverage.lower()} дня, риск дефицита {risk}. К заказу {format_integer_text(qty_number)} ед."

    overstock = format_percent_text(row.get("overstock_risk"))
    return f"Активная закупка не требуется: покрытие {coverage.lower()} дня, риск излишка {overstock}."


def build_business_purchase_plan_df(recommendations: pd.DataFrame | None) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=BUSINESS_PURCHASE_PLAN_COLUMNS)

    df = recommendations.copy()
    adjusted_qty = _coalesce_series(df, ["adjusted_order_qty", "recommended_order_qty"]).fillna(0)
    final_qty = _coalesce_series(df, ["final_order_qty", "adjusted_order_qty", "recommended_order_qty"]).fillna(0)
    supplier = _coalesce_series(df, ["supplier_name", "supplier"]).fillna("Поставщик не указан")
    reason = df.apply(build_business_reason, axis=1)
    status = _coalesce_series(df, ["status"]).fillna("new").map(localize_value)
    comment = _coalesce_series(df, ["comment"]).fillna("")

    business_df = pd.DataFrame(
        {
            "SKU": _series_or_default(df, "sku", ""),
            "Товар": _series_or_default(df, "product_name", ""),
            "Категория": _series_or_default(df, "category", ""),
            "Поставщик": supplier,
            "Приоритет": _series_or_default(df, "priority", "").map(localize_value),
            "Остаток": pd.to_numeric(_series_or_default(df, "current_stock", 0), errors="coerce").fillna(0),
            "Дней покрытия": pd.to_numeric(_series_or_default(df, "stock_days_left", 0), errors="coerce").fillna(0),
            "Риск дефицита": _series_or_default(df, "stockout_risk_label", "").map(localize_value),
            "Рекомендовано системой": pd.to_numeric(_series_or_default(df, "recommended_order_qty", 0), errors="coerce").fillna(0),
            "С учётом поставщика": pd.to_numeric(adjusted_qty, errors="coerce").fillna(0),
            "Итоговое количество": pd.to_numeric(final_qty, errors="coerce").fillna(0),
            "Причина": reason,
            "Статус": status,
            "Комментарий": comment,
        }
    )

    return business_df


def format_business_purchase_plan_for_export(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    export_df = df.copy()
    export_df["Приоритет"] = export_df["Приоритет"].map(localize_value)
    export_df["Статус"] = export_df["Статус"].map(localize_value)
    export_df["Остаток"] = export_df["Остаток"].map(format_integer_text)
    export_df["Дней покрытия"] = export_df["Дней покрытия"].map(lambda value: format_days_text(value).replace(" дн.", ""))
    export_df["Рекомендовано системой"] = export_df["Рекомендовано системой"].map(lambda value: format_quantity_text(value).replace(" ед.", ""))
    export_df["С учётом поставщика"] = export_df["С учётом поставщика"].map(lambda value: format_quantity_text(value).replace(" ед.", ""))
    export_df["Итоговое количество"] = export_df["Итоговое количество"].map(lambda value: format_quantity_text(value).replace(" ед.", ""))
    export_df["Риск дефицита"] = export_df["Риск дефицита"].map(localize_value)
    export_df["Причина"] = export_df["Причина"].map(lambda value: shorten_text(value, 120))
    return export_df


def build_business_purchase_plan_export_df(recommendations: pd.DataFrame | None) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=BUSINESS_PURCHASE_PLAN_COLUMNS)

    export_df = build_business_purchase_plan_df(recommendations)
    risk_values = pd.to_numeric(_series_or_default(recommendations, "stockout_risk", 0), errors="coerce").fillna(0)
    export_df["Риск дефицита"] = risk_values.map(format_percent_text)
    return format_business_purchase_plan_for_export(export_df)


def build_technical_recommendations_df(recommendations: pd.DataFrame | None) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["Сообщение"])

    df = recommendations.copy()
    for column in [
        "type",
        "action_group",
        "priority",
        "stockout_risk_label",
        "overstock_risk_label",
        "forecast_model",
        "confidence_label",
        "demand_pattern",
    ]:
        if column in df.columns:
            df[column] = localize_series(df[column])

    rename_columns = {
        "sku": "SKU",
        "product_name": "Товар",
        "category": "Категория",
        "type": "Тип рекомендации",
        "action_group": "Группа действия",
        "priority": "Приоритет",
        "current_stock": "Текущий остаток",
        "stock_days_left": "Дней покрытия",
        "days_of_cover": "Покрытие, дней",
        "average_daily_demand": "Средний спрос в день",
        "predicted_quantity": "Прогноз спроса, ед.",
        "recommended_order_qty": "Рекомендуемое количество",
        "expected_revenue": "Ожидаемая выручка",
        "safety_stock": "Страховой запас",
        "lead_time_demand": "Спрос на срок поставки",
        "reorder_point": "Точка заказа",
        "target_stock_level": "Целевой запас",
        "inventory_gap": "Разрыв по запасу",
        "service_level": "Уровень сервиса",
        "stockout_risk": "Риск дефицита",
        "stockout_risk_label": "Уровень риска дефицита",
        "overstock_risk": "Риск излишка",
        "overstock_risk_label": "Уровень риска излишка",
        "forecast_model": "Модель прогноза",
        "confidence_score": "Скор надёжности",
        "confidence_label": "Надёжность прогноза",
        "demand_pattern": "Паттерн спроса",
        "qty_if_lead_time_plus_2": "Если срок поставки +2 дня",
        "qty_if_safety_stock_plus_10pct": "Если страховой запас +10%",
        "qty_if_demand_growth_10pct": "Если спрос +10%",
        "message": "Короткая рекомендация",
        "explanation": "Пояснение",
    }
    df = df.rename(columns=rename_columns)
    return df


def build_abc_xyz_export_df(items: list[dict[str, Any]], *, localized: bool = True) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=ABC_XYZ_BUSINESS_COLUMNS if localized else [])

    df = pd.DataFrame(items)
    if localized:
        df = pd.DataFrame(
            {
                "SKU": _series_or_default(df, "sku", ""),
                "Товар": _series_or_default(df, "product_name", ""),
                "Категория": _series_or_default(df, "category", ""),
                "ABC": _series_or_default(df, "abc_class", ""),
                "XYZ": _series_or_default(df, "xyz_class", ""),
                "Класс ABC/XYZ": _series_or_default(df, "abc_xyz_class", ""),
                "Приоритет": _series_or_default(df, "management_priority", "").map(localize_value),
                "Выручка": pd.to_numeric(_series_or_default(df, "total_revenue", 0), errors="coerce").fillna(0),
                "Продано, ед.": pd.to_numeric(_series_or_default(df, "total_quantity_sold", 0), errors="coerce").fillna(0),
                "Доля выручки, %": pd.to_numeric(_series_or_default(df, "revenue_share_percent", 0), errors="coerce").fillna(0),
                "Накопленная доля, %": pd.to_numeric(_series_or_default(df, "cumulative_share_percent", 0), errors="coerce").fillna(0),
                "Средний спрос в день": pd.to_numeric(_series_or_default(df, "average_daily_demand", 0), errors="coerce").fillna(0),
                "Вариативность спроса, %": pd.to_numeric(_series_or_default(df, "coefficient_of_variation", 0), errors="coerce").fillna(0),
                "Действие": _series_or_default(df, "management_action", ""),
            }
        )
        return df

    return df


def format_abc_xyz_export_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    export_df = df.copy()
    for column in ["Выручка", "Продано, ед."]:
        if column in export_df.columns:
            export_df[column] = export_df[column].map(format_integer_text)
    for column in ["Доля выручки, %", "Накопленная доля, %", "Вариативность спроса, %"]:
        if column in export_df.columns:
            export_df[column] = export_df[column].map(format_percent_text)
    if "Средний спрос в день" in export_df.columns:
        export_df["Средний спрос в день"] = export_df["Средний спрос в день"].map(
            lambda value: "Нет данных"
            if to_number(value) is None
            else f"{to_number(value):,.1f}".replace(",", " ").replace(".", ",")
        )
    export_df["Приоритет"] = export_df["Приоритет"].map(localize_value)
    export_df["Действие"] = export_df["Действие"].map(shorten_text)
    return export_df


def build_abc_xyz_summary_df(summary: dict[str, Any]) -> pd.DataFrame:
    if not summary:
        return pd.DataFrame(columns=["Класс", "SKU", "Выручка", "Доля выручки, %", "Приоритет", "Действие"])

    rows = []
    for class_name, values in summary.items():
        rows.append(
            {
                "Класс": class_name,
                "SKU": values.get("products_count", 0),
                "Выручка": values.get("total_revenue", 0),
                "Доля выручки, %": values.get("revenue_share_percent", 0),
                "Приоритет": localize_value(values.get("management_priority")),
                "Действие": values.get("management_action", ""),
            }
        )

    return pd.DataFrame(rows)


def build_reliability_distribution_df(analysis_reliability: dict[str, Any] | None) -> pd.DataFrame:
    labels = ["high", "medium", "low", "insufficient_data"]
    counts = {label: 0 for label in labels}
    for item in (analysis_reliability or {}).get("sku_reliability", []) or []:
        confidence = str(item.get("confidence", "insufficient_data"))
        if confidence not in counts:
            confidence = "insufficient_data"
        counts[confidence] += 1

    return pd.DataFrame(
        {
            "Надёжность": ["Высокая", "Средняя", "Низкая", "Недостаточно данных"],
            "SKU": [counts[label] for label in labels],
        }
    )


def build_top_risks_df(recommendations: pd.DataFrame | None, limit: int = 5) -> pd.DataFrame:
    if recommendations is None or recommendations.empty:
        return pd.DataFrame(columns=["SKU", "Товар", "Приоритет", "Риск", "Остаток", "Дней покрытия", "К заказу", "Действие"])

    df = recommendations.copy()
    df = df.sort_values(
        by=["stockout_risk", "recommended_order_qty"],
        ascending=[False, False],
    ).head(limit)
    return pd.DataFrame(
        {
            "SKU": _series_or_default(df, "sku", ""),
            "Товар": _series_or_default(df, "product_name", ""),
            "Приоритет": _series_or_default(df, "priority", "").map(localize_value),
            "Риск": pd.to_numeric(_series_or_default(df, "stockout_risk", 0), errors="coerce").fillna(0),
            "Остаток": pd.to_numeric(_series_or_default(df, "current_stock", 0), errors="coerce").fillna(0),
            "Дней покрытия": pd.to_numeric(_series_or_default(df, "stock_days_left", 0), errors="coerce").fillna(0),
            "К заказу": pd.to_numeric(_series_or_default(df, "recommended_order_qty", 0), errors="coerce").fillna(0),
            "Действие": df.apply(
                lambda row: (
                    f"Проверьте остаток и закажите {format_integer_text(row.get('recommended_order_qty'))} ед."
                    if (to_number(row.get("recommended_order_qty")) or 0) > 0
                    else "Проверьте остаток и спрос вручную."
                ),
                axis=1,
            ),
        }
    )


def _coalesce_series(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    available = [column for column in columns if column in df.columns]
    if not available:
        return pd.Series(index=df.index, dtype="object")

    series = df[available[0]]
    for column in available[1:]:
        series = series.fillna(df[column])
    return series


def _series_or_default(df: pd.DataFrame, column: str, default: Any) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)
