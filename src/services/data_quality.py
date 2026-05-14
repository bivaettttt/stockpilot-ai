from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from src.domain.constants import (
    BOOLEAN_COLUMNS,
    DEFAULT_CATEGORY,
    NUMERIC_COLUMNS,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    TEXT_COLUMNS,
)
from src.domain.models import DataQualityProfile, ValidationIssue, ValidationReport

PLACEHOLDER_TEXT_VALUES = {"", "nan", "none", "null", "n/a", "na", "-"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_df = df.copy()
    normalized_df.columns = [str(column).strip().lower() for column in normalized_df.columns]
    return normalized_df


def prepare_sales_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    prepared_df = normalize_columns(df).copy()

    if "date" in prepared_df.columns:
        prepared_df["date"] = _coerce_dates(prepared_df["date"])

    for column in NUMERIC_COLUMNS:
        if column in prepared_df.columns:
            prepared_df[column] = _coerce_numeric(prepared_df[column])

    for column in TEXT_COLUMNS:
        if column in prepared_df.columns:
            prepared_df[column] = _clean_text_series(prepared_df[column])

    for column in BOOLEAN_COLUMNS:
        if column in prepared_df.columns:
            prepared_df[column] = _coerce_boolean(prepared_df[column])

    if "category" not in prepared_df.columns:
        prepared_df["category"] = DEFAULT_CATEGORY

    if "purchase_price" not in prepared_df.columns:
        prepared_df["purchase_price"] = 0.0

    if "selling_price" not in prepared_df.columns:
        prepared_df["selling_price"] = _calculate_selling_price_from_revenue(prepared_df)

    if "supplier" not in prepared_df.columns:
        prepared_df["supplier"] = ""

    if "promotion_flag" not in prepared_df.columns:
        prepared_df["promotion_flag"] = False

    prepared_df["category"] = prepared_df["category"].replace("", DEFAULT_CATEGORY).fillna(
        DEFAULT_CATEGORY
    )
    prepared_df["supplier"] = prepared_df["supplier"].fillna("")
    prepared_df["promotion_flag"] = prepared_df["promotion_flag"].fillna(False)
    prepared_df["purchase_price"] = prepared_df["purchase_price"].fillna(0.0)
    prepared_df["selling_price"] = prepared_df["selling_price"].fillna(
        _calculate_selling_price_from_revenue(prepared_df)
    )

    sortable_columns = [column for column in ["date", "sku"] if column in prepared_df.columns]
    if sortable_columns:
        prepared_df = prepared_df.sort_values(sortable_columns).reset_index(drop=True)

    return prepared_df


def validate_sales_dataframe(df: pd.DataFrame) -> ValidationReport:
    if df.empty:
        issue = ValidationIssue(
            severity="error",
            code="empty_file",
            message="Файл пустой. Добавьте строки с продажами и остатками.",
            suggestion="Добавьте хотя бы одну строку с датой, SKU, продажами и остатком.",
        )
        profile = DataQualityProfile(
            total_rows=0,
            completeness_score=0.0,
            validity_score=0.0,
            consistency_score=0.0,
            errors_count=1,
        )
        return ValidationReport(
            is_valid=False,
            errors=[issue.message],
            warnings=[],
            issues=[issue],
            data_quality=profile,
        )

    normalized_df = normalize_columns(df)
    issues: list[ValidationIssue] = []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in normalized_df.columns]
    if missing_columns:
        issues.append(
            ValidationIssue(
                severity="error",
                code="missing_required_columns",
                message="Не хватает обязательных колонок: " + ", ".join(missing_columns) + ".",
                suggestion="Проверьте шаблон файла и верните отсутствующие колонки.",
            )
        )
        return _build_report(
            normalized_df=normalized_df,
            issues=issues,
            missing_required_values=0,
            invalid_date_rows=0,
            invalid_numeric_rows=0,
            negative_value_rows=0,
            duplicate_rows=0,
            outlier_rows=0,
            inconsistent_rows=0,
        )

    missing_required_values = 0
    invalid_date_rows = 0
    invalid_numeric_rows = 0
    negative_value_rows = 0
    duplicate_rows = 0
    outlier_rows = 0
    inconsistent_rows = 0

    required_value_issues, missing_required_values = _validate_required_values(normalized_df)
    issues.extend(required_value_issues)

    date_issues, invalid_date_rows = _validate_dates(normalized_df)
    issues.extend(date_issues)

    numeric_issues, invalid_numeric_rows = _validate_numeric_columns(normalized_df)
    issues.extend(numeric_issues)

    negative_issues, negative_value_rows = _validate_non_negative_values(normalized_df)
    issues.extend(negative_issues)

    duplicate_issues, duplicate_rows = _validate_duplicates(normalized_df)
    issues.extend(duplicate_issues)

    identifier_issues = _validate_identifiers(normalized_df)
    issues.extend(identifier_issues)

    outlier_issues, outlier_rows = _validate_outliers(normalized_df)
    issues.extend(outlier_issues)

    consistency_issues, inconsistent_rows = _validate_consistency(normalized_df)
    issues.extend(consistency_issues)

    warnings = _detect_contextual_warnings(normalized_df)
    issues.extend(warnings)

    return _build_report(
        normalized_df=normalized_df,
        issues=issues,
        missing_required_values=missing_required_values,
        invalid_date_rows=invalid_date_rows,
        invalid_numeric_rows=invalid_numeric_rows,
        negative_value_rows=negative_value_rows,
        duplicate_rows=duplicate_rows,
        outlier_rows=outlier_rows,
        inconsistent_rows=inconsistent_rows,
    )


def _build_report(
    normalized_df: pd.DataFrame,
    issues: list[ValidationIssue],
    missing_required_values: int,
    invalid_date_rows: int,
    invalid_numeric_rows: int,
    negative_value_rows: int,
    duplicate_rows: int,
    outlier_rows: int,
    inconsistent_rows: int,
) -> ValidationReport:
    errors = [issue.message for issue in issues if issue.severity == "error"]
    warnings = [issue.message for issue in issues if issue.severity == "warning"]

    total_rows = len(normalized_df)
    required_cells = max(total_rows * len(REQUIRED_COLUMNS), 1)
    completeness_score = max(
        0.0,
        round(100 * (1 - missing_required_values / required_cells), 1),
    )
    validity_penalty = invalid_date_rows + invalid_numeric_rows + negative_value_rows
    validity_score = max(
        0.0,
        round(100 * (1 - validity_penalty / max(total_rows * 3, 1)), 1),
    )
    consistency_penalty = duplicate_rows + inconsistent_rows
    consistency_score = max(
        0.0,
        round(100 * (1 - consistency_penalty / max(total_rows * 2, 1)), 1),
    )

    data_quality = DataQualityProfile(
        total_rows=total_rows,
        completeness_score=completeness_score,
        validity_score=validity_score,
        consistency_score=consistency_score,
        duplicate_rows=duplicate_rows,
        missing_required_values=missing_required_values,
        invalid_date_rows=invalid_date_rows,
        invalid_numeric_rows=invalid_numeric_rows,
        negative_value_rows=negative_value_rows,
        outlier_rows=outlier_rows,
        inconsistent_rows=inconsistent_rows,
        warnings_count=len(warnings),
        errors_count=len(errors),
    )

    return ValidationReport(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        issues=issues,
        data_quality=data_quality,
    )


def _validate_required_values(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    missing_count = 0

    for column in REQUIRED_COLUMNS:
        column_series = df[column]
        empty_mask = column_series.isna()

        if column in TEXT_COLUMNS:
            empty_mask = empty_mask | _normalize_text_series(column_series).isin(PLACEHOLDER_TEXT_VALUES)

        issue_count = int(empty_mask.sum())
        if issue_count <= 0:
            continue

        missing_count += issue_count
        issues.append(
            ValidationIssue(
                severity="error",
                code="missing_required_values",
                message=f"В колонке '{column}' есть пустые значения: {issue_count} строк.",
                column=column,
                affected_rows=issue_count,
                suggestion=f"Заполните пустые значения в колонке '{column}'.",
            )
        )

    return issues, missing_count


def _validate_dates(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    parsed_dates = _coerce_dates(df["date"])
    invalid_mask = parsed_dates.isna()
    invalid_count = int(invalid_mask.sum())

    if invalid_count <= 0:
        return [], 0

    samples = _sample_values(df.loc[invalid_mask, "date"])
    return (
        [
            ValidationIssue(
                severity="error",
                code="invalid_dates",
                message=(
                    "В колонке 'date' есть некорректные даты: "
                    f"{invalid_count} строк. Используйте формат YYYY-MM-DD."
                ),
                column="date",
                affected_rows=invalid_count,
                sample_values=samples,
                suggestion="Приведите даты к единому формату ISO, например 2026-01-31.",
            )
        ],
        invalid_count,
    )


def _validate_numeric_columns(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    invalid_total = 0

    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue

        raw_values = df[column]
        numeric_values = _coerce_numeric(raw_values)
        invalid_mask = numeric_values.isna() & raw_values.notna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count <= 0:
            continue

        invalid_total += invalid_count
        issues.append(
            ValidationIssue(
                severity="error",
                code="invalid_numeric",
                message=f"В колонке '{column}' есть нечисловые значения: {invalid_count} строк.",
                column=column,
                affected_rows=invalid_count,
                sample_values=_sample_values(raw_values[invalid_mask]),
                suggestion=f"Удалите валютные символы и убедитесь, что '{column}' содержит числа.",
            )
        )

    return issues, invalid_total


def _validate_non_negative_values(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    negative_total = 0

    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue

        numeric_values = _coerce_numeric(df[column])
        negative_mask = numeric_values < 0
        negative_count = int(negative_mask.sum())

        if negative_count <= 0:
            continue

        negative_total += negative_count
        issues.append(
            ValidationIssue(
                severity="error",
                code="negative_values",
                message=f"В колонке '{column}' есть отрицательные значения: {negative_count} строк.",
                column=column,
                affected_rows=negative_count,
                suggestion="Исправьте отрицательные значения или вынесите возвраты в отдельный поток данных.",
            )
        )

    return issues, negative_total


def _validate_duplicates(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    parsed_dates = _coerce_dates(df["date"])
    if parsed_dates.isna().any():
        return [], 0

    duplicate_check_df = df.copy()
    duplicate_check_df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    duplicate_check_df["sku"] = _normalize_text_series(duplicate_check_df["sku"])

    duplicate_mask = duplicate_check_df.duplicated(subset=["date", "sku"], keep=False)
    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count <= 0:
        return [], 0

    return (
        [
            ValidationIssue(
                severity="error",
                code="duplicate_date_sku",
                message=(
                    "Найдены дубли по связке date + sku: "
                    f"{duplicate_count} строк. Для одного товара в один день должна быть одна строка."
                ),
                affected_rows=duplicate_count,
                suggestion="Схлопните дубли в одну строку по каждому SKU и дате.",
            )
        ],
        duplicate_count,
    )


def _validate_identifiers(df: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    sku_series = _normalize_text_series(df["sku"])
    suspicious_sku_mask = sku_series.str.len() < 3
    suspicious_sku_count = int(suspicious_sku_mask.sum())
    if suspicious_sku_count > 0:
        issues.append(
            ValidationIssue(
                severity="warning",
                code="weak_sku_identifier",
                message=(
                    f"У {suspicious_sku_count} SKU слишком короткий идентификатор. "
                    "Проверьте, что артикулы не потерялись при экспорте."
                ),
                column="sku",
                affected_rows=suspicious_sku_count,
                sample_values=_sample_values(sku_series[suspicious_sku_mask]),
                suggestion="Используйте стабильные артикулы длиной хотя бы 3 символа.",
            )
        )

    if "category" in df.columns:
        category_series = _normalize_text_series(df["category"])
        missing_category_mask = category_series.isin(PLACEHOLDER_TEXT_VALUES)
        missing_category_count = int(missing_category_mask.sum())
        if missing_category_count > 0:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="missing_category",
                    message=(
                        f"У {missing_category_count} строк не заполнена категория. "
                        "Аналитика по категориям будет менее полезной."
                    ),
                    column="category",
                    affected_rows=missing_category_count,
                    suggestion="Заполните категорию, чтобы улучшить сегментацию ассортимента.",
                )
            )

    return issues


def _validate_outliers(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    issues: list[ValidationIssue] = []
    outlier_rows: set[int] = set()

    for column in ["quantity_sold", "revenue"]:
        series = _coerce_numeric(df[column]).dropna()
        if len(series) < 8:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        if iqr <= 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_mask = (_coerce_numeric(df[column]) < lower_bound) | (
            _coerce_numeric(df[column]) > upper_bound
        )
        count = int(outlier_mask.sum())
        if count <= 0:
            continue

        outlier_rows.update(df.index[outlier_mask].tolist())
        issues.append(
            ValidationIssue(
                severity="warning",
                code="outliers_detected",
                message=(
                    f"В колонке '{column}' найдены выбросы: {count} строк. "
                    "Проверьте аномально большие или маленькие значения."
                ),
                column=column,
                affected_rows=count,
                sample_values=_sample_values(df.loc[outlier_mask, column]),
                suggestion="Проверьте, не попали ли в файл возвраты, оптовые сделки или ошибки выгрузки.",
            )
        )

    return issues, len(outlier_rows)


def _validate_consistency(df: pd.DataFrame) -> tuple[list[ValidationIssue], int]:
    if "selling_price" not in df.columns:
        return [], 0

    quantity = _coerce_numeric(df["quantity_sold"])
    revenue = _coerce_numeric(df["revenue"])
    selling_price = _coerce_numeric(df["selling_price"])

    expected_revenue = quantity * selling_price
    valid_mask = quantity.gt(0) & selling_price.gt(0) & revenue.notna()
    if not valid_mask.any():
        return [], 0

    diff_ratio = ((revenue - expected_revenue).abs() / expected_revenue.clip(lower=1)).where(
        valid_mask,
        other=0,
    )
    inconsistent_mask = diff_ratio > 0.2
    inconsistent_count = int(inconsistent_mask.sum())

    if inconsistent_count <= 0:
        return [], 0

    return (
        [
            ValidationIssue(
                severity="warning",
                code="revenue_price_mismatch",
                message=(
                    f"У {inconsistent_count} строк выручка заметно расходится с quantity_sold * selling_price."
                ),
                affected_rows=inconsistent_count,
                suggestion="Проверьте, одинаково ли трактуются скидки, НДС и промо-цены в источнике данных.",
            )
        ],
        inconsistent_count,
    )


def _detect_contextual_warnings(df: pd.DataFrame) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if "date" in df.columns:
        parsed_dates = _coerce_dates(df["date"]).dropna()
        if not parsed_dates.empty:
            span_days = int((parsed_dates.max() - parsed_dates.min()).days) + 1
            if span_days < 21:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="short_history_window",
                        message=(
                            f"История продаж покрывает только {span_days} дн. "
                            "Прогноз будет менее устойчивым, особенно для сезонных SKU."
                        ),
                        suggestion="По возможности загрузите минимум 4-8 недель истории.",
                    )
                )

    if "promotion_flag" in df.columns:
        promo_share = float(_coerce_boolean(df["promotion_flag"]).mean())
        if promo_share > 0.5:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="high_promo_share",
                    message=(
                        "Более половины строк отмечены как промо. "
                        "Базовый спрос без промо может отличаться от наблюдаемого."
                    ),
                    suggestion="Используйте поле promotion_flag для интерпретации всплесков спроса.",
                )
            )

    return issues


def _coerce_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed")


def _coerce_numeric(series: pd.Series) -> pd.Series:
    normalized = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"nan": None, "None": None, "": None})
    )
    return pd.to_numeric(normalized, errors="coerce")


def _coerce_boolean(series: pd.Series) -> pd.Series:
    normalized = _normalize_text_series(series)
    return normalized.isin({"1", "true", "yes", "y", "да", "promo", "акция"})


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _normalize_text_series(series: pd.Series) -> pd.Series:
    return _clean_text_series(series).str.lower()


def _sample_values(values: Iterable[Any], limit: int = 3) -> list[str]:
    samples: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text.lower() == "nan":
            continue
        samples.append(text)
        if len(samples) >= limit:
            break
    return samples


def _calculate_selling_price_from_revenue(df: pd.DataFrame) -> pd.Series:
    quantity = _coerce_numeric(df["quantity_sold"]).replace(0, pd.NA)
    revenue = _coerce_numeric(df["revenue"])
    selling_price = revenue / quantity
    return selling_price.fillna(0.0)


def list_known_columns() -> list[str]:
    return REQUIRED_COLUMNS + [column for column in OPTIONAL_COLUMNS if column not in REQUIRED_COLUMNS]
