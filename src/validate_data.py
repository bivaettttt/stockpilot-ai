from __future__ import annotations

import pandas as pd

from src.domain.constants import (
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
)
from src.domain.constants import (
    OPTIONAL_COLUMNS as _OPTIONAL_COLUMNS,
)
from src.domain.models import ValidationReport
from src.services.data_quality import (
    list_known_columns,
    normalize_columns,
    prepare_sales_dataframe,
    validate_sales_dataframe,
)

OPTIONAL_COLUMNS = _OPTIONAL_COLUMNS


def validate_sales_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Проверяет входной файл продаж и остатков.

    Возвращает:
    - is_valid: bool
    - errors: list[str]

    Файл считается валидным, если:
    - есть все обязательные колонки;
    - дата корректно преобразуется;
    - критичные поля не пустые;
    - числовые поля можно преобразовать в числа;
    - продажи, выручка и остатки не отрицательные;
    - нет дублей по date + sku.
    """
    report = validate_sales_dataframe(df)
    return report.is_valid, report.errors


def get_validation_report(df: pd.DataFrame) -> ValidationReport:
    return validate_sales_dataframe(df)


def prepare_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Подготавливает данные к аналитике:

    - нормализует названия колонок;
    - приводит date к datetime;
    - приводит числовые колонки к numeric;
    - очищает текстовые поля;
    - добавляет category, если её нет;
    - добавляет purchase_price/selling_price, если их нет;
    - сортирует данные по date и sku.
    """
    return prepare_sales_dataframe(df)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_columns(df)


def _get_missing_required_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in REQUIRED_COLUMNS if column not in df.columns]


def _validate_required_values(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            continue

        empty_count = df[column].isna().sum()

        if empty_count > 0:
            errors.append(f"В колонке '{column}' есть пустые значения: {empty_count} строк.")

    for column in ["sku", "product_name"]:
        if column not in df.columns:
            continue

        empty_string_count = (
            df[column].astype(str).str.strip().isin(["", "nan", "none", "null"]).sum()
        )

        if empty_string_count > 0:
            errors.append(
                f"В колонке '{column}' есть пустые текстовые значения: {empty_string_count} строк."
            )

    return errors


def _validate_dates(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    invalid_count = parsed_dates.isna().sum()

    if invalid_count > 0:
        errors.append(
            "В колонке 'date' есть некорректные даты: "
            f"{invalid_count} строк. Используйте формат YYYY-MM-DD."
        )

    return errors


def _validate_numeric_columns(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue

        numeric_values = pd.to_numeric(df[column], errors="coerce")
        invalid_count = numeric_values.isna().sum()

        if invalid_count > 0:
            errors.append(f"В колонке '{column}' есть нечисловые значения: {invalid_count} строк.")

    return errors


def _validate_non_negative_values(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    columns_to_check = [
        "quantity_sold",
        "revenue",
        "stock_on_hand",
        "purchase_price",
        "selling_price",
    ]

    for column in columns_to_check:
        if column not in df.columns:
            continue

        numeric_values = pd.to_numeric(df[column], errors="coerce")

        if numeric_values.isna().any():
            continue

        negative_count = (numeric_values < 0).sum()

        if negative_count > 0:
            errors.append(
                f"В колонке '{column}' есть отрицательные значения: {negative_count} строк."
            )

    return errors


def _validate_duplicates(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    parsed_dates = pd.to_datetime(df["date"], errors="coerce")

    if parsed_dates.isna().any():
        return errors

    duplicate_check_df = df.copy()
    duplicate_check_df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    duplicate_check_df["sku"] = duplicate_check_df["sku"].astype(str).str.strip()

    duplicate_count = duplicate_check_df.duplicated(
        subset=["date", "sku"],
        keep=False,
    ).sum()

    if duplicate_count > 0:
        errors.append(
            "Найдены дубли по связке date + sku: "
            f"{duplicate_count} строк. Для одного товара в один день должна быть одна строка."
        )

    return errors


def _calculate_selling_price_from_revenue(df: pd.DataFrame) -> pd.Series:
    prepared = prepare_sales_dataframe(df)
    return prepared["selling_price"]


def get_supported_columns() -> list[str]:
    return list_known_columns()
