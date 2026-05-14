from __future__ import annotations

from typing import Any


ALLOWED_CONTEXT_KEYS = {
    "stage",
    "filename",
    "columns",
    "required_columns_status",
    "optional_columns_status",
    "suggested_mapping",
    "validation_errors",
    "validation_warnings",
    "warnings",
    "is_ready_for_analysis",
    "sample_rows",
}

ANALYSIS_ALLOWED_CONTEXT_KEYS = {
    "stage",
    "summary",
    "kpis",
    "top_recommendations",
    "high_risk_items",
    "overstock_items",
    "exceptions",
    "forecast_quality",
    "data_quality",
    "reliability_warnings",
    "purchase_plan_decisions",
    "selected_sku",
}


def build_import_assist_context(raw_context: dict[str, Any] | None) -> dict[str, Any]:
    context = raw_context or {}
    compact: dict[str, Any] = {
        "stage": _as_string(context.get("stage")) or "upload_mapping",
        "filename": _as_string(context.get("filename")) or "unknown",
        "columns": _limit_string_list(context.get("columns"), 50),
        "required_columns_status": _sanitize_status_dict(context.get("required_columns_status")),
        "optional_columns_status": _sanitize_status_dict(context.get("optional_columns_status")),
        "suggested_mapping": _sanitize_mapping(context.get("suggested_mapping")),
        "validation_errors": _sanitize_messages(context.get("validation_errors")),
        "validation_warnings": _sanitize_messages(context.get("validation_warnings")),
        "warnings": _sanitize_messages(context.get("warnings")),
        "is_ready_for_analysis": bool(context.get("is_ready_for_analysis", False)),
        "sample_rows": _sanitize_sample_rows(context.get("sample_rows")),
    }
    return {key: value for key, value in compact.items() if key in ALLOWED_CONTEXT_KEYS}


def build_analysis_assist_context(raw_context: dict[str, Any] | None) -> dict[str, Any]:
    context = raw_context or {}
    compact: dict[str, Any] = {
        "stage": _as_string(context.get("stage")) or "analysis",
        "summary": _sanitize_summary(context.get("summary")),
        "kpis": _sanitize_object(context.get("kpis"), limit=15),
        "top_recommendations": _sanitize_records(context.get("top_recommendations"), limit=15),
        "high_risk_items": _sanitize_records(context.get("high_risk_items"), limit=15),
        "overstock_items": _sanitize_records(context.get("overstock_items"), limit=15),
        "exceptions": _sanitize_records(context.get("exceptions"), limit=15),
        "forecast_quality": _sanitize_object(context.get("forecast_quality"), limit=20),
        "data_quality": _sanitize_object(context.get("data_quality"), limit=20),
        "reliability_warnings": _sanitize_messages(context.get("reliability_warnings")),
        "purchase_plan_decisions": _sanitize_records(context.get("purchase_plan_decisions"), limit=15),
        "selected_sku": _sanitize_object(context.get("selected_sku"), limit=20),
    }
    return {key: value for key, value in compact.items() if key in ANALYSIS_ALLOWED_CONTEXT_KEYS}


def _as_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _limit_string_list(value: Any, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:limit]]


def _sanitize_status_dict(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}

    sanitized: dict[str, dict[str, Any]] = {}
    for key, payload in value.items():
        if not isinstance(payload, dict):
            continue
        sanitized[str(key)] = {
            "present": bool(payload.get("present", False)),
            "source_column": _as_string(payload.get("source_column")),
        }
    return sanitized


def _sanitize_mapping(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}

    sanitized: dict[str, dict[str, Any]] = {}
    for key, payload in value.items():
        if not isinstance(payload, dict):
            continue
        confidence_raw = payload.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0
        sanitized[str(key)] = {
            "source_column": _as_string(payload.get("source_column")),
            "confidence": max(0.0, min(1.0, confidence)),
            "status": _as_string(payload.get("status")) or "missing",
        }
    return sanitized


def _sanitize_messages(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    sanitized: list[dict[str, Any]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        sanitized.append(
            {
                "code": _as_string(item.get("code")) or "unknown",
                "field": _as_string(item.get("field")),
                "title": _as_string(item.get("title")) or "",
                "message": _as_string(item.get("message")) or "",
                "suggestion": _as_string(item.get("suggestion")),
            }
        )
    return sanitized


def _sanitize_sample_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    rows: list[dict[str, Any]] = []
    for row in value[:5]:
        if not isinstance(row, dict):
            continue
        limited_row: dict[str, Any] = {}
        for key, cell in list(row.items())[:12]:
            if isinstance(cell, (str, int, float, bool)) or cell is None:
                limited_row[str(key)] = cell
            else:
                limited_row[str(key)] = str(cell)
        rows.append(limited_row)
    return rows


def _sanitize_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "filename": _as_string(value.get("filename")),
        "period": _as_string(value.get("period")),
        "sku_count": _coerce_number(value.get("sku_count")),
        "row_count": _coerce_number(value.get("row_count")),
    }


def _sanitize_object(value: Any, *, limit: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for key, item in list(value.items())[:limit]:
        normalized_key = str(key)
        if isinstance(item, (str, int, float, bool)) or item is None:
            result[normalized_key] = item
        elif isinstance(item, dict):
            result[normalized_key] = _sanitize_object(item, limit=limit)
        elif isinstance(item, list):
            result[normalized_key] = _sanitize_records(item, limit=min(limit, 10))
        else:
            result[normalized_key] = str(item)
    return result


def _sanitize_records(value: Any, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in value[:limit]:
        if not isinstance(item, dict):
            continue
        sanitized_row: dict[str, Any] = {}
        for key, cell in list(item.items())[:20]:
            if isinstance(cell, (str, int, float, bool)) or cell is None:
                sanitized_row[str(key)] = cell
            else:
                sanitized_row[str(key)] = str(cell)
        rows.append(sanitized_row)
    return rows


def _coerce_number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    return None
