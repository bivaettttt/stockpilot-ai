from __future__ import annotations

from pathlib import Path
import json
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from src.api.json_sanitize import sanitize_json_value
from src.api.schemas import (
    ErrorResponse,
    ImportInspectResponse,
    SuggestMappingResponse,
    ValidateMappingResponse,
)
from src.api.utils import dataframe_to_records, save_upload_file_with_metadata
from src.import_wizard import (
    dataframe_to_csv_bytes,
    normalize_dataset,
    suggest_mapping,
    validate_mapping_payload,
)
from src.import_wizard.schema import CANONICAL_COLUMN_ORDER
from src.load_data import load_sales_data
from src.logger import setup_logger
from src.validate_data import OPTIONAL_COLUMNS, REQUIRED_COLUMNS

logger = setup_logger()
router = APIRouter(tags=["Import"])


@router.post(
    "/import/inspect",
    response_model=ImportInspectResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def inspect_import_file(file: UploadFile = File(...)) -> ImportInspectResponse:
    request_id = uuid4().hex[:8]

    try:
        upload = await save_upload_file_with_metadata(file)
        raw_df = load_sales_data(upload.path)

        required_columns_status = _build_column_status(list(raw_df.columns), REQUIRED_COLUMNS)
        optional_columns_status = _build_column_status(list(raw_df.columns), OPTIONAL_COLUMNS)
        warnings = _build_inspect_warnings(raw_df, required_columns_status)
        blocking_warning_codes = {"missing_required_column", "empty_dataset", "date_not_parsed"}
        is_ready_for_analysis = (
            all(status["present"] for status in required_columns_status.values())
            and not any(warning["code"] in blocking_warning_codes for warning in warnings)
        )

        inspected = sanitize_json_value(
            {
                "filename": upload.original_filename,
                "file_type": Path(upload.original_filename).suffix.lower().lstrip("."),
                "row_count": len(raw_df),
                "column_count": len(raw_df.columns),
                "columns": list(raw_df.columns),
                "sample_rows": dataframe_to_records(raw_df.head(10)),
                "required_columns_status": required_columns_status,
                "optional_columns_status": optional_columns_status,
                "date_range": _build_date_range(raw_df),
                "sku_count": _build_sku_count(raw_df),
                "warnings": warnings,
                "is_ready_for_analysis": is_ready_for_analysis,
                "human_readable_summary": _build_human_summary(
                    filename=upload.original_filename,
                    row_count=len(raw_df),
                    column_count=len(raw_df.columns),
                    missing_required_columns=[
                        column
                        for column, status in required_columns_status.items()
                        if not status["present"]
                    ],
                ),
            }
        )
        return ImportInspectResponse(**inspected)

    except ValueError as error:
        logger.warning("API import inspect failed. Request ID: %s. Error: %s", request_id, error)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(error),
                "errors": [str(error)],
                "request_id": request_id,
            },
        )

    except Exception as error:
        logger.exception("API import inspect failed. Request ID: %s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(error),
                "errors": None,
                "request_id": request_id,
            },
        )


def _build_column_status(
    columns: list[str],
    target_columns: list[str],
) -> dict[str, dict[str, str | bool | None]]:
    available_columns = set(columns)
    return {
        column: {
            "present": column in available_columns,
            "source_column": column if column in available_columns else None,
        }
        for column in target_columns
    }


def _build_date_range(raw_df: pd.DataFrame) -> dict[str, str | None] | None:
    if "date" not in raw_df.columns:
        return None

    parsed_dates = pd.to_datetime(raw_df["date"], errors="coerce")
    valid_dates = parsed_dates.dropna()
    if valid_dates.empty:
        return None

    return {
        "min": valid_dates.min().strftime("%Y-%m-%d"),
        "max": valid_dates.max().strftime("%Y-%m-%d"),
    }


def _build_sku_count(raw_df: pd.DataFrame) -> int | None:
    if "sku" not in raw_df.columns:
        return None

    sku_series = raw_df["sku"].fillna("").astype(str).str.strip()
    return int(sku_series[sku_series != ""].nunique())


def _build_inspect_warnings(
    raw_df: pd.DataFrame,
    required_columns_status: dict[str, dict[str, str | bool | None]],
) -> list[dict[str, str | None]]:
    warnings: list[dict[str, str | None]] = []

    required_column_copy = {
        "date": ("Дата", "Без date StockPilot не сможет собрать хронологию продаж и построить прогноз.", "Добавьте колонку date или используйте шаблон файла."),
        "sku": ("Артикул", "Без sku StockPilot не сможет разделить данные по товарам и посчитать рекомендации по SKU.", "Добавьте колонку sku или используйте шаблон файла."),
        "product_name": ("Название товара", "Без product_name будет сложнее читать результаты и проверять рекомендации по товарам.", "Добавьте колонку product_name или используйте шаблон файла."),
        "quantity_sold": ("Продажи", "Без quantity_sold StockPilot не сможет оценить спрос и динамику продаж.", "Добавьте колонку quantity_sold или используйте шаблон файла."),
        "revenue": ("Выручка", "Без revenue StockPilot не сможет показать вклад SKU и категории в продажи.", "Добавьте колонку revenue или используйте шаблон файла."),
        "stock_on_hand": ("Остаток", "Без stock_on_hand StockPilot не сможет оценить риск дефицита и рассчитать покрытие запасов.", "Добавьте колонку stock_on_hand или используйте шаблон файла."),
    }

    for field, status in required_columns_status.items():
        if status["present"]:
            continue
        title_label, message, suggestion = required_column_copy[field]
        warnings.append(
            {
                "code": "missing_required_column",
                "field": field,
                "title": f"Не хватает колонки «{title_label}»",
                "message": message,
                "suggestion": suggestion,
            }
        )

    if raw_df.empty:
        warnings.append(
            {
                "code": "empty_dataset",
                "field": None,
                "title": "Файл не содержит строк с данными",
                "message": "StockPilot увидел структуру файла, но не нашёл строк для анализа.",
                "suggestion": "Проверьте, что файл содержит данные ниже заголовка колонок.",
            }
        )

    if "date" in raw_df.columns:
        parsed_dates = pd.to_datetime(raw_df["date"], errors="coerce")
        if parsed_dates.notna().sum() == 0:
            warnings.append(
                {
                    "code": "date_not_parsed",
                    "field": "date",
                    "title": "Не удалось распознать даты",
                    "message": "Колонка date найдена, но значения не удалось прочитать как даты.",
                    "suggestion": "Используйте формат YYYY-MM-DD или проверьте содержимое колонки date.",
                }
            )

    return warnings


def _build_human_summary(
    *,
    filename: str,
    row_count: int,
    column_count: int,
    missing_required_columns: list[str],
) -> str:
    if not missing_required_columns:
        return (
            f"Файл {filename} содержит {row_count} строк и {column_count} колонок. "
            "Все обязательные поля найдены, файл готов к анализу."
        )

    missing_columns_text = ", ".join(missing_required_columns)
    return (
        f"Файл {filename} содержит {row_count} строк и {column_count} колонок. "
        f"Для запуска анализа не хватает обязательных полей: {missing_columns_text}."
    )


@router.post(
    "/import/suggest-mapping",
    response_model=SuggestMappingResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def suggest_import_mapping(file: UploadFile = File(...)) -> SuggestMappingResponse:
    request_id = uuid4().hex[:8]

    try:
        upload = await save_upload_file_with_metadata(file)
        raw_df = load_sales_data(upload.path)
        mapping, warnings = suggest_mapping(list(raw_df.columns))
        is_ready_for_normalization = all(
            mapping[field].source_column is not None
            for field in REQUIRED_COLUMNS
        )

        suggested = sanitize_json_value(
            {
                "filename": upload.original_filename,
                "columns": list(raw_df.columns),
                "suggested_mapping": {
                    field: {
                        "source_column": candidate.source_column,
                        "confidence": candidate.confidence,
                        "status": candidate.status,
                    }
                    for field, candidate in mapping.items()
                },
                "warnings": warnings,
                "is_ready_for_normalization": is_ready_for_normalization,
            }
        )
        return SuggestMappingResponse(**suggested)

    except ValueError as error:
        logger.warning("API suggest-mapping failed. Request ID: %s. Error: %s", request_id, error)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(error),
                "errors": [str(error)],
                "request_id": request_id,
            },
        )
    except Exception as error:
        logger.exception("API suggest-mapping failed. Request ID: %s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(error),
                "errors": None,
                "request_id": request_id,
            },
        )


@router.post(
    "/import/validate-mapping",
    response_model=ValidateMappingResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def validate_import_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(...),
) -> ValidateMappingResponse:
    request_id = uuid4().hex[:8]

    try:
        upload = await save_upload_file_with_metadata(file)
        raw_df = load_sales_data(upload.path)
        mapping_payload = _parse_mapping_payload(mapping)
        is_valid, errors, warnings, normalized_mapping, summary = validate_mapping_payload(
            raw_df,
            mapping_payload,
        )

        validated = sanitize_json_value(
            {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "mapping": normalized_mapping,
                "human_readable_summary": summary,
            }
        )
        return ValidateMappingResponse(**validated)

    except ValueError as error:
        logger.warning("API validate-mapping failed. Request ID: %s. Error: %s", request_id, error)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(error),
                "errors": [str(error)],
                "request_id": request_id,
            },
        )
    except Exception as error:
        logger.exception("API validate-mapping failed. Request ID: %s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(error),
                "errors": None,
                "request_id": request_id,
            },
        )


@router.post(
    "/import/normalize",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def normalize_import_file(
    file: UploadFile = File(...),
    mapping: str = Form(...),
) -> Response:
    request_id = uuid4().hex[:8]

    try:
        upload = await save_upload_file_with_metadata(file)
        raw_df = load_sales_data(upload.path)
        mapping_payload = _parse_mapping_payload(mapping)
        is_valid, errors, _, normalized_mapping, _ = validate_mapping_payload(raw_df, mapping_payload)
        if not is_valid:
            raise ValueError(errors[0]["message"] if errors else "Сопоставление не прошло проверку.")

        normalized_df = normalize_dataset(raw_df, normalized_mapping)
        csv_bytes = dataframe_to_csv_bytes(normalized_df)
        filename = f"{Path(upload.original_filename).stem}_normalized.csv"

        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as error:
        logger.warning("API normalize import failed. Request ID: %s. Error: %s", request_id, error)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(error),
                "errors": [str(error)],
                "request_id": request_id,
            },
        )
    except Exception as error:
        logger.exception("API normalize import failed. Request ID: %s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(error),
                "errors": None,
                "request_id": request_id,
            },
        )


def _parse_mapping_payload(raw_mapping: str) -> dict[str, dict[str, object] | str | None]:
    try:
        parsed = json.loads(raw_mapping)
    except json.JSONDecodeError as error:
        raise ValueError("Не удалось прочитать JSON с сопоставлением колонок.") from error

    if not isinstance(parsed, dict):
        raise ValueError("Сопоставление колонок должно быть JSON-объектом.")

    return {
        field: parsed.get(field)
        for field in CANONICAL_COLUMN_ORDER
    }
