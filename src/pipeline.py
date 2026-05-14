import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.analytics import (
    calculate_category_sales,
    calculate_daily_sales,
    calculate_product_sales,
    calculate_summary_metrics,
    get_low_stock_products,
    get_overstock_products,
    get_top_products_by_revenue,
)
from src.api.abc import build_abc_analysis, build_abc_summary
from src.api.portfolio import build_abc_xyz_matrix, build_abc_xyz_summary
from src.api.xyz import build_xyz_analysis, build_xyz_summary
from src.config import AppConfig
from src.export_dashboard import export_dashboard_html
from src.export_report import export_analysis_report
from src.forecast import build_daily_forecast_chart_data, build_product_forecast
from src.load_data import load_sales_data
from src.logger import setup_logger
from src.recommendations import (
    build_business_insights,
    build_purchase_recommendations,
)
from src.services.analytics_service import build_analytics_snapshot
from src.services.reliability_service import build_analysis_reliability
from src.services.recommendation_service import build_category_recommendations
from src.validate_data import get_validation_report, prepare_sales_data

logger = setup_logger()


@dataclass
class AnalysisResult:
    """
    Результат полного анализа StockPilot AI.

    Этот объект позже можно будет отдавать через API во frontend.
    """

    summary_metrics: dict[str, Any]
    insights: list[str]
    daily_sales: pd.DataFrame
    product_sales: pd.DataFrame
    category_sales: pd.DataFrame
    top_products: pd.DataFrame
    low_stock_products: pd.DataFrame
    overstock_products: pd.DataFrame
    product_forecast: pd.DataFrame
    daily_forecast_chart_data: pd.DataFrame
    recommendations: pd.DataFrame
    category_recommendations: list[dict[str, Any]]
    analytics_snapshot: dict[str, list[dict[str, Any]]]
    abc_analysis: list[dict[str, Any]]
    abc_summary: dict[str, Any]
    xyz_analysis: list[dict[str, Any]]
    xyz_summary: dict[str, Any]
    abc_xyz_matrix: list[dict[str, Any]]
    abc_xyz_summary: dict[str, Any]
    data_quality: dict[str, Any]
    analysis_reliability: dict[str, Any]
    validation_warnings: list[str]
    report_path: Path
    dashboard_path: Path
    analysis_duration_ms: int


class DataValidationError(Exception):
    """
    Ошибка валидации входных данных.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = "Данные не прошли проверку: " + "; ".join(errors)
        super().__init__(message)


def run_stockpilot_pipeline(config: AppConfig) -> AnalysisResult:
    """
    Запускает полный pipeline анализа.

    Этапы:
    1. загрузка данных;
    2. валидация;
    3. подготовка типов данных;
    4. расчёт аналитики;
    5. прогнозирование;
    6. построение рекомендаций;
    7. экспорт Excel-отчёта;
    8. экспорт HTML-дашборда.
    """
    started_at = time.perf_counter()
    logger.info("Pipeline started")
    logger.info("Input file: %s", config.input_file)
    logger.info("Output file: %s", config.output_file)
    logger.info("Dashboard file: %s", config.dashboard_file)
    logger.info("Forecast horizon days: %s", config.forecast_horizon_days)
    logger.info("Safety stock percent: %s", config.safety_stock_percent)
    logger.info("Supply lead time days: %s", config.supply_lead_time_days)

    raw_df = load_sales_data(config.input_file)

    logger.info("File loaded successfully. Rows: %s", len(raw_df))

    validation_report = get_validation_report(raw_df)

    if not validation_report.is_valid:
        logger.warning("Data validation failed: %s", validation_report.errors)
        raise DataValidationError(validation_report.errors)

    prepared_df = prepare_sales_data(raw_df)

    logger.info("Data validation passed")

    summary_metrics = calculate_summary_metrics(prepared_df)
    daily_sales = calculate_daily_sales(prepared_df)
    product_sales = calculate_product_sales(prepared_df)
    category_sales = calculate_category_sales(prepared_df)

    top_products = get_top_products_by_revenue(product_sales)
    low_stock_products = get_low_stock_products(product_sales)
    overstock_products = get_overstock_products(product_sales)

    product_forecast = build_product_forecast(
        prepared_df,
        horizon_days=config.forecast_horizon_days,
    )

    daily_forecast_chart_data = build_daily_forecast_chart_data(
        prepared_df,
        horizon_days=config.forecast_horizon_days,
    )

    recommendations = build_purchase_recommendations(
        product_forecast=product_forecast,
        safety_stock_percent=config.safety_stock_percent,
        supply_lead_time_days=config.supply_lead_time_days,
    )

    category_recommendations = build_category_recommendations(recommendations)
    analytics_snapshot = build_analytics_snapshot(
        df=prepared_df,
        product_sales=product_sales,
        recommendations=recommendations,
    )
    analysis_reliability = build_analysis_reliability(
        prepared_df=prepared_df,
        product_forecast=product_forecast,
        data_quality=validation_report.data_quality.to_dict(),
        horizon_days=config.forecast_horizon_days,
    )

    insights = build_business_insights(
        product_sales=product_sales,
        product_forecast=product_forecast,
        recommendations=recommendations,
    )

    abc_analysis = build_abc_analysis(product_sales.to_dict(orient="records"))
    abc_summary = build_abc_summary(abc_analysis)
    xyz_analysis = build_xyz_analysis(prepared_df)
    xyz_summary = build_xyz_summary(xyz_analysis)
    abc_xyz_matrix = build_abc_xyz_matrix(abc_analysis=abc_analysis, xyz_analysis=xyz_analysis)
    abc_xyz_summary = build_abc_xyz_summary(abc_xyz_matrix)

    report_path = export_analysis_report(
        output_file=config.output_file,
        source_filename=config.input_file.name,
        generated_at=pd.Timestamp.now(),
        parameters={
            "horizon": config.forecast_horizon_days,
            "safety_stock": config.safety_stock_percent,
            "lead_time": config.supply_lead_time_days,
        },
        summary_metrics=summary_metrics,
        insights=insights,
        daily_sales=daily_sales,
        product_sales=product_sales,
        category_sales=category_sales,
        product_forecast=product_forecast,
        daily_forecast_chart_data=daily_forecast_chart_data,
        recommendations=recommendations,
        abc_analysis=abc_analysis,
        abc_summary=abc_summary,
        xyz_analysis=xyz_analysis,
        xyz_summary=xyz_summary,
        abc_xyz_matrix=abc_xyz_matrix,
        abc_xyz_summary=abc_xyz_summary,
        data_quality=validation_report.data_quality.to_dict(),
        analysis_reliability=analysis_reliability,
        category_recommendations=category_recommendations,
        analytics_snapshot=analytics_snapshot,
    )

    dashboard_path = export_dashboard_html(
        output_file=config.dashboard_file,
        summary_metrics=summary_metrics,
        insights=insights,
        product_sales=product_sales,
        product_forecast=product_forecast,
        category_sales=category_sales,
        daily_sales=daily_sales,
        daily_forecast_chart_data=daily_forecast_chart_data,
        recommendations=recommendations,
        abc_xyz_matrix=abc_xyz_matrix,
        abc_xyz_summary=abc_xyz_summary,
        data_quality=validation_report.data_quality.to_dict(),
        analysis_reliability=analysis_reliability,
        source_filename=config.input_file.name,
        generated_at=pd.Timestamp.now(),
        parameters={
            "horizon": config.forecast_horizon_days,
            "safety_stock": config.safety_stock_percent,
            "lead_time": config.supply_lead_time_days,
        },
    )

    logger.info("Report exported successfully: %s", report_path)
    logger.info("Dashboard exported successfully: %s", dashboard_path)
    logger.info("Pipeline finished successfully")

    analysis_duration_ms = int((time.perf_counter() - started_at) * 1000)

    return AnalysisResult(
        summary_metrics=summary_metrics,
        insights=insights,
        daily_sales=daily_sales,
        product_sales=product_sales,
        category_sales=category_sales,
        top_products=top_products,
        low_stock_products=low_stock_products,
        overstock_products=overstock_products,
        product_forecast=product_forecast,
        daily_forecast_chart_data=daily_forecast_chart_data,
        recommendations=recommendations,
        category_recommendations=category_recommendations,
        analytics_snapshot=analytics_snapshot,
        abc_analysis=abc_analysis,
        abc_summary=abc_summary,
        xyz_analysis=xyz_analysis,
        xyz_summary=xyz_summary,
        abc_xyz_matrix=abc_xyz_matrix,
        abc_xyz_summary=abc_xyz_summary,
        data_quality=validation_report.data_quality.to_dict(),
        analysis_reliability=analysis_reliability,
        validation_warnings=validation_report.warnings,
        report_path=report_path,
        dashboard_path=dashboard_path,
        analysis_duration_ms=analysis_duration_ms,
    )
