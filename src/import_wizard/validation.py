from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from src.domain.constants import NUMERIC_COLUMNS, OPTIONAL_COLUMNS, REQUIRED_COLUMNS
from src.import_wizard.column_mapper import normalize_column_name
from src.import_wizard.schema import CANONICAL_FIELD_LABELS


def validate_mapping_payload(
    raw_df: pd.DataFrame,
    mapping: dict[str, dict[str, Any] | str | None],
) -> tuple[bool, list[dict[str, str | None]], list[dict[str, str | None]], dict[str, dict[str, Any]], str]:
    columns = list(raw_df.columns)
    column_lookup = {normalize_column_name(column): column for column in columns}
    normalized_mapping = _normalize_mapping(mapping, column_lookup)

    errors: list[dict[str, str | None]] = []
    warnings: list[dict[str, str | None]] = []

    for field in REQUIRED_COLUMNS:
        source_column = normalized_mapping.get(field, {}).get("source_column")
        if not source_column:
            errors.append(
                _message(
                    code="missing_required_mapping",
                    field=field,
                    title=f"Не хватает обязательного поля «{CANONICAL_FIELD_LABELS[field]}»",
                    message=f"Не удалось сопоставить обязательное поле «{CANONICAL_FIELD_LABELS[field]}».",
                    suggestion="Выберите подходящую колонку вручную.",
                )
            )

    for field, payload in normalized_mapping.items():
        source_column = payload.get("source_column")
        if source_column and source_column not in columns:
            errors.append(
                _message(
                    code="missing_source_column",
                    field=field,
                    title=f"Колонка для поля «{CANONICAL_FIELD_LABELS.get(field, field)}» не найдена",
                    message=f"В файле нет колонки «{source_column}».",
                    suggestion="Выберите колонку из текущего файла.",
                )
            )

    mapped_sources = [
        payload["source_column"]
        for payload in normalized_mapping.values()
        if payload.get("source_column")
    ]
    duplicates = [column for column, count in Counter(mapped_sources).items() if count > 1]
    for duplicate in duplicates:
        errors.append(
            _message(
                code="duplicate_source_mapping",
                field=None,
                title="Одна колонка назначена нескольким полям",
                message=f"Колонка «{duplicate}» выбрана сразу для нескольких полей StockPilot.",
                suggestion="Назначьте каждой колонке только одно целевое поле.",
            )
        )

    for field, payload in normalized_mapping.items():
        source_column = payload.get("source_column")
        if not source_column or source_column not in raw_df.columns:
            continue

        if field == "date":
            if pd.to_datetime(raw_df[source_column], errors="coerce").notna().sum() == 0:
                errors.append(
                    _message(
                        code="date_column_not_valid",
                        field=field,
                        title="Колонка даты не похожа на даты",
                        message=f"Колонка «{source_column}» не читается как дата.",
                        suggestion="Проверьте формат значений. Лучше использовать YYYY-MM-DD.",
                    )
                )

        if field in NUMERIC_COLUMNS:
            numeric_values = pd.to_numeric(raw_df[source_column], errors="coerce")
            if numeric_values.notna().sum() == 0:
                errors.append(
                    _message(
                        code="numeric_column_not_valid",
                        field=field,
                        title=f"Колонка «{CANONICAL_FIELD_LABELS[field]}» не похожа на числа",
                        message=f"Колонка «{source_column}» не содержит читаемых числовых значений.",
                        suggestion="Проверьте значения и уберите текст из числовой колонки.",
                    )
                )

        if field in {"sku", "product_name"}:
            non_empty = (
                raw_df[source_column]
                .fillna("")
                .astype(str)
                .str.strip()
                .replace({"nan": "", "None": ""})
            )
            if (non_empty != "").sum() == 0:
                errors.append(
                    _message(
                        code="text_column_empty",
                        field=field,
                        title=f"Колонка «{CANONICAL_FIELD_LABELS[field]}» пустая",
                        message=f"Колонка «{source_column}» не содержит значений, пригодных для анализа.",
                        suggestion="Выберите другую колонку или исправьте исходный файл.",
                    )
                )

    for field in OPTIONAL_COLUMNS:
        if not normalized_mapping.get(field, {}).get("source_column"):
            continue
        if field == "promotion_flag":
            warnings.append(
                _message(
                    code="promotion_flag_review",
                    field=field,
                    title="Проверьте колонку «Промо»",
                    message="StockPilot постарается привести значения promo к true/false во время нормализации.",
                    suggestion="Если в колонке текстовые отметки, проверьте результат после нормализации.",
                )
            )

    is_valid = len(errors) == 0
    summary = (
        "Сопоставление прошло проверку. Файл можно нормализовать."
        if is_valid
        else "Сопоставление требует исправлений перед нормализацией."
    )
    return is_valid, errors, warnings, normalized_mapping, summary


def _normalize_mapping(
    mapping: dict[str, dict[str, Any] | str | None],
    column_lookup: dict[str, str],
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for field in [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]:
        payload = mapping.get(field)
        source_column: str | None = None
        confidence = 0.0
        status = "missing"

        if isinstance(payload, dict):
            raw_source = payload.get("source_column")
            if isinstance(raw_source, str):
                source_column = column_lookup.get(normalize_column_name(raw_source), raw_source)
            confidence = float(payload.get("confidence", 0.0) or 0.0)
            status = str(payload.get("status", "matched" if source_column else "missing"))
        elif isinstance(payload, str):
            source_column = column_lookup.get(normalize_column_name(payload), payload)
            status = "matched"

        normalized[field] = {
            "source_column": source_column,
            "confidence": confidence,
            "status": status,
        }

    return normalized


def _message(
    *,
    code: str,
    field: str | None,
    title: str,
    message: str,
    suggestion: str | None,
) -> dict[str, str | None]:
    return {
        "code": code,
        "field": field,
        "title": title,
        "message": message,
        "suggestion": suggestion,
    }
