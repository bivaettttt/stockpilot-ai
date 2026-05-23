from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from src.api.history import add_history_record, build_history_record
from src.api.json_sanitize import sanitize_json_value
from src.api.schemas import (
    AnalyzeResponse,
    ErrorResponse,
    ValidateFileResponse,
)
from src.api.utils import (
    API_OUTPUT_DIR,
    dataframe_to_records,
    save_upload_file_with_metadata,
)
from src.config import AppConfig
from src.load_data import load_sales_data
from src.logger import setup_logger
from src.pipeline import DataValidationError, run_stockpilot_pipeline
from src.report_presenter import (
    build_abc_xyz_export_df,
    build_business_purchase_plan_export_df,
    format_abc_xyz_export_for_csv,
)
from src.validate_data import (
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    get_validation_report,
)

logger = setup_logger()
router = APIRouter(tags=["Analysis"])


@router.post(
    "/validate-file",
    response_model=ValidateFileResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def validate_file(file: UploadFile = File(...)) -> ValidateFileResponse:
    request_id = uuid4().hex[:8]

    try:
        upload = await save_upload_file_with_metadata(file)
        raw_df = load_sales_data(upload.path)
        validation_report = get_validation_report(raw_df)

        columns_found = list(raw_df.columns)
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns_found]
        optional_columns_found = [column for column in OPTIONAL_COLUMNS if column in columns_found]

        status = "success" if validation_report.is_valid else "validation_failed"
        message = (
            "Файл прошёл предварительную проверку."
            if validation_report.is_valid
            else "Файл не прошёл предварительную проверку."
        )

        validated = sanitize_json_value(
            {
                "status": status,
                "message": message,
                "is_valid": validation_report.is_valid,
                "row_count": len(raw_df),
                "columns_found": columns_found,
                "required_columns": REQUIRED_COLUMNS,
                "missing_columns": missing_columns,
                "optional_columns": OPTIONAL_COLUMNS,
                "optional_columns_found": optional_columns_found,
                "errors": validation_report.errors,
                "warnings": validation_report.warnings,
                "issues": [issue.to_dict() for issue in validation_report.issues],
                "data_quality": validation_report.data_quality.to_dict(),
            }
        )
        return ValidateFileResponse(**validated)

    except ValueError as error:
        logger.warning("API validate-file failed. Request ID: %s. Error: %s", request_id, error)
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
        logger.exception("API validate-file failed. Request ID: %s", request_id)
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
    "/analyze",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    horizon: int = Form(14, ge=1, le=365),
    safety_stock: float = Form(0.2, ge=0),
    lead_time: int = Form(3, ge=0),
) -> AnalyzeResponse:
    request_id = uuid4().hex[:8]

    try:
        logger.info("API analyze request started. Request ID: %s", request_id)
        upload = await save_upload_file_with_metadata(file)

        output_file = API_OUTPUT_DIR / f"report_{request_id}.xlsx"
        dashboard_file = API_OUTPUT_DIR / f"dashboard_{request_id}.html"
        recommendations_csv_file = API_OUTPUT_DIR / f"recommendations_{request_id}.csv"
        recommendations_raw_csv_file = API_OUTPUT_DIR / f"recommendations_raw_{request_id}.csv"
        abc_xyz_matrix_csv_file = API_OUTPUT_DIR / f"abc_xyz_matrix_{request_id}.csv"

        config = AppConfig(
            input_file=upload.path,
            output_file=output_file,
            dashboard_file=dashboard_file,
            forecast_horizon_days=horizon,
            safety_stock_percent=safety_stock,
            supply_lead_time_days=lead_time,
        )

        result = run_stockpilot_pipeline(config)

        build_business_purchase_plan_export_df(result.recommendations).to_csv(
            recommendations_csv_file,
            index=False,
            encoding="utf-8-sig",
        )
        result.recommendations.to_csv(
            recommendations_raw_csv_file,
            index=False,
            encoding="utf-8-sig",
        )

        report_filename = Path(result.report_path).name
        dashboard_filename = Path(result.dashboard_path).name
        recommendations_csv_filename = recommendations_csv_file.name
        abc_xyz_matrix_csv_filename = abc_xyz_matrix_csv_file.name

        base_url = str(request.base_url).rstrip("/")
        report_url = f"{base_url}/files/report/{report_filename}"
        dashboard_url = f"{base_url}/files/dashboard/{dashboard_filename}"
        recommendations_csv_url = f"{base_url}/files/recommendations/{recommendations_csv_filename}"
        recommendations_raw_csv_url = f"{base_url}/files/recommendations-raw/{recommendations_raw_csv_file.name}"
        abc_xyz_matrix_csv_url = f"{base_url}/files/abc-xyz/{abc_xyz_matrix_csv_filename}"

        recommendations = dataframe_to_records(result.recommendations)
        top_products = dataframe_to_records(result.top_products)
        product_forecast = dataframe_to_records(result.product_forecast)
        category_sales = dataframe_to_records(result.category_sales)
        daily_sales = dataframe_to_records(result.daily_sales)
        daily_forecast_chart_data = dataframe_to_records(result.daily_forecast_chart_data)

        abc_analysis = result.abc_analysis
        abc_summary = result.abc_summary
        xyz_analysis = result.xyz_analysis
        xyz_summary = result.xyz_summary
        abc_xyz_matrix = result.abc_xyz_matrix
        abc_xyz_summary = result.abc_xyz_summary

        _export_abc_xyz_matrix_csv(file_path=abc_xyz_matrix_csv_file, matrix=abc_xyz_matrix)

        history_record = build_history_record(
            request_id=request_id,
            original_filename=upload.original_filename,
            horizon=horizon,
            safety_stock=safety_stock,
            lead_time=lead_time,
            summary_metrics=result.summary_metrics,
            recommendations_count=len(recommendations),
            report_path=str(Path(result.report_path)),
            dashboard_path=str(Path(result.dashboard_path)),
            report_url=report_url,
            dashboard_url=dashboard_url,
            recommendations_csv_path=str(recommendations_csv_file),
            recommendations_csv_url=recommendations_csv_url,
            abc_xyz_matrix_csv_path=str(abc_xyz_matrix_csv_file),
            abc_xyz_matrix_csv_url=abc_xyz_matrix_csv_url,
            status="success",
            file_hash=upload.file_hash,
            data_quality=result.data_quality,
            analysis_duration_ms=result.analysis_duration_ms,
        )
        created_at = history_record["created_at"]

        analyzed = sanitize_json_value(
            {
                "run_id": request_id,
                "status": "success",
                "message": "Анализ выполнен успешно.",
                "original_filename": upload.original_filename,
                "created_at": created_at,
                "parameters": {
                    "horizon": horizon,
                    "safety_stock": safety_stock,
                    "lead_time": lead_time,
                },
                "summary_metrics": result.summary_metrics,
                "insights": result.insights,
                "recommendations": recommendations,
                "category_recommendations": result.category_recommendations,
                "top_products": top_products,
                "daily_sales": daily_sales,
                "product_forecast": product_forecast,
                "daily_forecast_chart_data": daily_forecast_chart_data,
                "category_sales": category_sales,
                "analytics_snapshot": result.analytics_snapshot,
                "abc_analysis": abc_analysis,
                "abc_summary": abc_summary,
                "xyz_analysis": xyz_analysis,
                "xyz_summary": xyz_summary,
                "abc_xyz_matrix": abc_xyz_matrix,
                "abc_xyz_summary": abc_xyz_summary,
                "data_quality": result.data_quality,
                "analysis_reliability": result.analysis_reliability,
                "warnings": result.validation_warnings,
                "analysis_duration_ms": result.analysis_duration_ms,
                "report_path": str(Path(result.report_path)),
                "dashboard_path": str(Path(result.dashboard_path)),
                "recommendations_csv_path": str(recommendations_csv_file),
                "recommendations_raw_csv_path": str(recommendations_raw_csv_file),
                "abc_xyz_matrix_csv_path": str(abc_xyz_matrix_csv_file),
                "report_url": report_url,
                "dashboard_url": dashboard_url,
                "recommendations_csv_url": recommendations_csv_url,
                "recommendations_raw_csv_url": recommendations_raw_csv_url,
                "abc_xyz_matrix_csv_url": abc_xyz_matrix_csv_url,
            }
        )
        history_record["result_snapshot"] = analyzed
        add_history_record(history_record)
        return AnalyzeResponse(**analyzed)

    except DataValidationError as error:
        logger.warning(
            "API data validation failed. Request ID: %s. Errors: %s",
            request_id,
            error.errors,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Данные не прошли проверку.",
                "errors": error.errors,
                "request_id": request_id,
            },
        )

    except Exception as error:
        logger.exception("API analysis failed. Request ID: %s", request_id)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(error),
                "errors": None,
                "request_id": request_id,
            },
        )


def _export_abc_xyz_matrix_csv(file_path: Path, matrix: list[dict[str, Any]]) -> None:
    df = format_abc_xyz_export_for_csv(build_abc_xyz_export_df(matrix, localized=True))
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
