from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pandas as pd

from src.report_presenter import (
    build_abc_xyz_export_df,
    build_abc_xyz_summary_df,
    build_business_purchase_plan_df,
    build_reliability_distribution_df,
    build_technical_recommendations_df,
    build_top_risks_df,
    format_integer_text,
    format_money_text,
    format_percent_text,
    format_quantity_text,
    localize_forecast_confidence,
    localize_value,
    shorten_text,
)

DEFAULT_OUTPUT_FILE = Path("data/output/stockpilot_report.xlsx")
DASHBOARD_DATA_SHEET = "_dashboard_data"

SHEET_NAMES = {
    "summary": "Сводка",
    "data_quality": "Проблемы данных",
    "reliability": "Надёжность анализа",
    "insights": "Выводы",
    "purchase_plan": "Закупочный план",
    "raw_recommendations": "Технические рекомендации",
    "category_actions": "Категории закупок",
    "risks": "Риски",
    "daily_sales": "Продажи по дням",
    "weekday_sales": "По дням недели",
    "monthly_sales": "По месяцам",
    "product_sales": "Товары",
    "category_sales": "Категории",
    "forecast": "Прогноз",
    "abc": "ABC анализ",
    "xyz": "XYZ анализ",
    "abc_xyz": "ABC XYZ матрица",
}

SUMMARY_METRIC_NAMES = {
    "total_revenue": "Общая выручка",
    "total_units_sold": "Продано единиц",
    "unique_products": "SKU в анализе",
    "unique_categories": "Категорий",
    "average_revenue_per_sale_row": "Средняя выручка на строку",
    "average_price_per_unit": "Средняя цена за единицу",
    "gross_profit": "Валовая прибыль",
    "gross_margin_percent": "Валовая маржинальность",
    "date_range_days": "Период, дней",
    "inventory_turnover_ratio": "Оборачиваемость запасов",
}


def safe_freeze_panes(worksheet, row: int = 0, col: int = 0) -> None:
    if row > 0 or col > 0:
        worksheet.freeze_panes(row, col)


def export_analysis_report(
    output_file: str | Path = DEFAULT_OUTPUT_FILE,
    *,
    source_filename: str | None = None,
    generated_at: Any | None = None,
    parameters: dict[str, Any] | None = None,
    summary_metrics: dict[str, Any] | None = None,
    insights: list[str] | None = None,
    daily_sales: pd.DataFrame | None = None,
    product_sales: pd.DataFrame | None = None,
    category_sales: pd.DataFrame | None = None,
    product_forecast: pd.DataFrame | None = None,
    daily_forecast_chart_data: pd.DataFrame | None = None,
    recommendations: pd.DataFrame | None = None,
    abc_analysis: list[dict[str, Any]] | None = None,
    abc_summary: dict[str, Any] | None = None,
    xyz_analysis: list[dict[str, Any]] | None = None,
    xyz_summary: dict[str, Any] | None = None,
    abc_xyz_matrix: list[dict[str, Any]] | None = None,
    abc_xyz_summary: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    analysis_reliability: dict[str, Any] | None = None,
    category_recommendations: list[dict[str, Any]] | None = None,
    analytics_snapshot: dict[str, list[dict[str, Any]]] | None = None,
) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_metrics = summary_metrics or {}
    insights = insights or []
    parameters = parameters or {}
    data_quality = data_quality or {}
    analysis_reliability = analysis_reliability or {}
    analytics_snapshot = analytics_snapshot or {}
    abc_analysis = abc_analysis or []
    xyz_analysis = xyz_analysis or []
    abc_xyz_matrix = abc_xyz_matrix or []
    abc_xyz_summary = abc_xyz_summary or {}

    prepared_summary = _prepare_summary(summary_metrics)
    prepared_data_quality = _prepare_data_quality(data_quality)
    prepared_reliability = _prepare_reliability_dataframe(analysis_reliability)
    prepared_insights = _prepare_insights(insights)
    prepared_purchase_plan = build_business_purchase_plan_df(recommendations)
    prepared_raw_recommendations = build_technical_recommendations_df(recommendations)
    prepared_risks = build_top_risks_df(recommendations, limit=25)
    prepared_category_actions = _prepare_records_dataframe(
        category_recommendations or [],
        empty_message="Нет категориальных рекомендаций.",
    )
    prepared_daily_sales = _prepare_dataframe(daily_sales)
    prepared_product_sales = _prepare_dataframe(product_sales)
    prepared_category_sales = _prepare_dataframe(category_sales)
    prepared_forecast = _prepare_dataframe(product_forecast)
    prepared_weekday_sales = _prepare_records_dataframe(
        analytics_snapshot.get("weekday_sales", []),
        empty_message="Нет среза по дням недели.",
    )
    prepared_monthly_sales = _prepare_records_dataframe(
        analytics_snapshot.get("monthly_sales", []),
        empty_message="Нет среза по месяцам.",
    )
    prepared_abc = _prepare_records_dataframe(abc_analysis, empty_message="Нет ABC-анализа.")
    prepared_xyz = _prepare_records_dataframe(xyz_analysis, empty_message="Нет XYZ-анализа.")
    prepared_abc_xyz = build_abc_xyz_export_df(abc_xyz_matrix, localized=True)
    if prepared_abc_xyz.empty:
        prepared_abc_xyz = pd.DataFrame(columns=["Сообщение"]).assign(Сообщение=["Нет ABC/XYZ-матрицы."])

    reliability_distribution = build_reliability_distribution_df(analysis_reliability)
    abc_distribution = build_abc_xyz_summary_df(abc_xyz_summary)
    category_chart_data = _prepare_chart_source(
        category_sales,
        value_columns=["category", "total_revenue"],
        rename={"category": "Категория", "total_revenue": "Выручка"},
        limit=6,
    )
    top_products_chart_data = _prepare_chart_source(
        product_sales,
        value_columns=["product_name", "total_revenue"],
        rename={"product_name": "Товар", "total_revenue": "Выручка"},
        limit=6,
    )
    forecast_chart_data = _prepare_forecast_chart_data(daily_forecast_chart_data)

    meta = _build_report_metadata(
        source_filename=source_filename,
        generated_at=generated_at,
        summary_metrics=summary_metrics,
        daily_sales=daily_sales,
        data_quality=data_quality,
        parameters=parameters,
    )

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        formats = _create_formats(workbook)

        summary_sheet = workbook.add_worksheet(SHEET_NAMES["summary"])
        writer.sheets[SHEET_NAMES["summary"]] = summary_sheet
        dashboard_data_sheet = workbook.add_worksheet(DASHBOARD_DATA_SHEET)
        writer.sheets[DASHBOARD_DATA_SHEET] = dashboard_data_sheet

        prepared_purchase_plan.to_excel(writer, sheet_name=SHEET_NAMES["purchase_plan"], index=False)
        prepared_reliability.to_excel(writer, sheet_name=SHEET_NAMES["reliability"], index=False)
        prepared_data_quality.to_excel(writer, sheet_name=SHEET_NAMES["data_quality"], index=False)
        prepared_insights.to_excel(writer, sheet_name=SHEET_NAMES["insights"], index=False)
        prepared_risks.to_excel(writer, sheet_name=SHEET_NAMES["risks"], index=False)
        prepared_category_actions.to_excel(writer, sheet_name=SHEET_NAMES["category_actions"], index=False)
        prepared_daily_sales.to_excel(writer, sheet_name=SHEET_NAMES["daily_sales"], index=False)
        prepared_weekday_sales.to_excel(writer, sheet_name=SHEET_NAMES["weekday_sales"], index=False)
        prepared_monthly_sales.to_excel(writer, sheet_name=SHEET_NAMES["monthly_sales"], index=False)
        prepared_product_sales.to_excel(writer, sheet_name=SHEET_NAMES["product_sales"], index=False)
        prepared_category_sales.to_excel(writer, sheet_name=SHEET_NAMES["category_sales"], index=False)
        prepared_forecast.to_excel(writer, sheet_name=SHEET_NAMES["forecast"], index=False)
        prepared_abc.to_excel(writer, sheet_name=SHEET_NAMES["abc"], index=False)
        prepared_xyz.to_excel(writer, sheet_name=SHEET_NAMES["xyz"], index=False)
        prepared_abc_xyz.to_excel(writer, sheet_name=SHEET_NAMES["abc_xyz"], index=False)
        prepared_raw_recommendations.to_excel(writer, sheet_name=SHEET_NAMES["raw_recommendations"], index=False)

        _write_summary_sheet(
            worksheet=summary_sheet,
            formats=formats,
            meta=meta,
            summary_metrics=summary_metrics,
            product_sales=prepared_product_sales,
            purchase_plan=prepared_purchase_plan,
            recommendations=recommendations,
            top_risks=prepared_risks.head(5),
            analysis_reliability=analysis_reliability,
            data_quality=data_quality,
        )
        _write_chart_sources(
            worksheet=dashboard_data_sheet,
            formats=formats,
            category_chart_data=category_chart_data,
            top_products_chart_data=top_products_chart_data,
            forecast_chart_data=forecast_chart_data,
            reliability_distribution=reliability_distribution,
            abc_distribution=abc_distribution,
        )
        _insert_summary_charts(
            workbook=workbook,
            worksheet=summary_sheet,
            chart_sources={
                "category": category_chart_data,
                "products": top_products_chart_data,
                "forecast": forecast_chart_data,
                "reliability": reliability_distribution,
                "abc": abc_distribution,
            },
            source_sheet_name=DASHBOARD_DATA_SHEET,
        )
        for sheet_name, worksheet in writer.sheets.items():
            if sheet_name in {SHEET_NAMES["summary"], DASHBOARD_DATA_SHEET}:
                continue
            _format_sheet_base(worksheet, formats)

        _format_purchase_plan_sheet(writer.sheets[SHEET_NAMES["purchase_plan"]], formats)
        _format_reliability_sheet(writer.sheets[SHEET_NAMES["reliability"]], formats)
        _format_data_quality_sheet(writer.sheets[SHEET_NAMES["data_quality"]], formats)
        _format_insights_sheet(writer.sheets[SHEET_NAMES["insights"]], formats)
        _format_risks_sheet(writer.sheets[SHEET_NAMES["risks"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["category_actions"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["daily_sales"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["weekday_sales"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["monthly_sales"]], formats)
        _format_product_sheet(writer.sheets[SHEET_NAMES["product_sales"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["category_sales"]], formats)
        _format_forecast_sheet(writer.sheets[SHEET_NAMES["forecast"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["abc"]], formats)
        _format_standard_sheet(writer.sheets[SHEET_NAMES["xyz"]], formats)
        _format_abc_xyz_sheet(writer.sheets[SHEET_NAMES["abc_xyz"]], formats)
        _format_raw_recommendations_sheet(writer.sheets[SHEET_NAMES["raw_recommendations"]], formats)

    return output_path


def _prepare_summary(summary_metrics: dict[str, Any]) -> pd.DataFrame:
    rows = [{"Показатель": SUMMARY_METRIC_NAMES.get(key, key), "Значение": value} for key, value in summary_metrics.items()]
    return pd.DataFrame(rows or [{"Показатель": "Нет данных", "Значение": ""}])


def _prepare_data_quality(data_quality: dict[str, Any]) -> pd.DataFrame:
    if not data_quality:
        return pd.DataFrame([{"Показатель": "Нет данных", "Значение": ""}])
    rows = [
        {"Показатель": "Всего строк", "Значение": data_quality.get("total_rows")},
        {"Показатель": "Полнота", "Значение": data_quality.get("completeness_score")},
        {"Показатель": "Корректность", "Значение": data_quality.get("validity_score")},
        {"Показатель": "Согласованность", "Значение": data_quality.get("consistency_score")},
        {"Показатель": "Предупреждения", "Значение": data_quality.get("warnings_count")},
        {"Показатель": "Ошибки", "Значение": data_quality.get("errors_count")},
        {"Показатель": "Дубликаты", "Значение": data_quality.get("duplicate_rows")},
        {"Показатель": "Пропуски в обязательных полях", "Значение": data_quality.get("missing_required_values")},
        {"Показатель": "Некорректные даты", "Значение": data_quality.get("invalid_date_rows")},
        {"Показатель": "Некорректные числа", "Значение": data_quality.get("invalid_numeric_rows")},
    ]
    return pd.DataFrame(rows)


def _prepare_reliability_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    if not payload:
        return pd.DataFrame([{"Показатель": "Нет данных по надёжности анализа", "Значение": ""}])

    forecast_quality = payload.get("forecast_quality", {}) or {}
    rows = [
        {"Показатель": "Надёжность прогноза", "Значение": localize_value(forecast_quality.get("overall_confidence"))},
        {"Показатель": "Индекс надёжности", "Значение": forecast_quality.get("reliability_score")},
        {"Показатель": "WAPE", "Значение": forecast_quality.get("wape")},
        {"Показатель": "MAE", "Значение": forecast_quality.get("mae")},
        {"Показатель": "Bias", "Значение": forecast_quality.get("bias")},
        {"Показатель": "Период backtest, дней", "Значение": forecast_quality.get("backtest_period_days")},
        {"Показатель": "Покрытие SKU", "Значение": forecast_quality.get("coverage")},
    ]
    for warning in (payload.get("warnings", []) or [])[:8]:
        title = warning.get("title") if isinstance(warning, dict) else str(warning)
        rows.append({"Показатель": "Предупреждение", "Значение": title})
    return pd.DataFrame(rows)


def _prepare_insights(insights: list[str]) -> pd.DataFrame:
    if not insights:
        return pd.DataFrame([{"№": 1, "Вывод": "Недостаточно данных для автоматической сводки."}])
    return pd.DataFrame([{"№": index + 1, "Вывод": insight} for index, insight in enumerate(insights)])


def _prepare_records_dataframe(records: list[dict[str, Any]], empty_message: str) -> pd.DataFrame:
    if not records:
        return pd.DataFrame([{"Сообщение": empty_message}])
    return pd.DataFrame(records)


def _prepare_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame([{"Сообщение": "Нет данных для отображения."}])

    prepared = df.copy()
    for column in prepared.columns:
        if pd.api.types.is_datetime64_any_dtype(prepared[column]):
            prepared[column] = prepared[column].dt.strftime("%d.%m.%Y")
    return prepared


def _prepare_chart_source(
    df: pd.DataFrame | None,
    *,
    value_columns: list[str],
    rename: dict[str, str],
    limit: int,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=list(rename.values()))
    result = df[value_columns].copy().head(limit).rename(columns=rename)
    return result


def _prepare_forecast_chart_data(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Дата", "Прогноз спроса"])
    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    prepared = (
        prepared.dropna(subset=["date"])
        .groupby("date", as_index=False)
        .agg(predicted_quantity=("predicted_quantity", "sum"))
        .sort_values("date")
        .head(14)
    )
    prepared["date"] = prepared["date"].dt.normalize()
    return prepared.rename(columns={"date": "Дата", "predicted_quantity": "Прогноз спроса"})


def _prepare_dashboard_value_chart_data(
    df: pd.DataFrame | None,
    label_column: str,
    value_column: str,
    label_name: str,
    value_name: str,
    limit: int,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[label_name, value_name])
    source_label = _first_existing_column(df, [label_column, label_name])
    source_value = _first_existing_column(df, [value_column, value_name])
    if source_label is None or source_value is None:
        return pd.DataFrame(columns=[label_name, value_name])
    prepared = df[[source_label, source_value]].copy()
    prepared[source_value] = pd.to_numeric(prepared[source_value], errors="coerce").fillna(0)
    prepared = prepared.sort_values(source_value, ascending=False).head(limit)
    return prepared.rename(columns={source_label: label_name, source_value: value_name})


def _prepare_daily_sales_chart_data(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Дата", "Выручка"])
    date_column = _first_existing_column(df, ["date", "Дата"])
    revenue_column = _first_existing_column(df, ["revenue", "Выручка", "total_revenue"])
    if date_column is None or revenue_column is None:
        return pd.DataFrame(columns=["Дата", "Выручка"])
    prepared = df[[date_column, revenue_column]].copy()
    prepared[date_column] = pd.to_datetime(prepared[date_column], errors="coerce")
    prepared[revenue_column] = pd.to_numeric(prepared[revenue_column], errors="coerce").fillna(0)
    prepared = (
        prepared.dropna(subset=[date_column])
        .groupby(date_column, as_index=False)
        .agg({revenue_column: "sum"})
        .sort_values(date_column)
        .tail(14)
    )
    prepared[date_column] = prepared[date_column].dt.normalize()
    return prepared.rename(columns={date_column: "Дата", revenue_column: "Выручка"})


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def _build_report_metadata(
    *,
    source_filename: str | None,
    generated_at: Any | None,
    summary_metrics: dict[str, Any],
    daily_sales: pd.DataFrame | None,
    data_quality: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    if generated_at is None:
        generated_at = pd.Timestamp.now()
    generated_at = pd.to_datetime(generated_at)

    if daily_sales is not None and not daily_sales.empty and "date" in daily_sales.columns:
        start_date = pd.to_datetime(daily_sales["date"], errors="coerce").min()
        end_date = pd.to_datetime(daily_sales["date"], errors="coerce").max()
    else:
        start_date = end_date = None

    return {
        "source_filename": source_filename or "Файл анализа",
        "generated_at": generated_at.strftime("%d.%m.%Y %H:%M"),
        "period": (
            f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
            if pd.notna(start_date) and pd.notna(end_date)
            else "Нет данных"
        ),
        "sku_count": int(summary_metrics.get("unique_products", 0) or 0),
        "row_count": int(data_quality.get("total_rows", 0) or 0),
        "horizon": int(parameters.get("horizon", 0) or 0),
        "safety_stock": parameters.get("safety_stock"),
        "lead_time": parameters.get("lead_time"),
    }


def _write_dashboard_sheet(
    *,
    worksheet,
    workbook,
    formats: dict[str, Any],
    meta: dict[str, Any],
    summary_metrics: dict[str, Any],
    product_sales: pd.DataFrame,
    category_sales: pd.DataFrame,
    daily_sales: pd.DataFrame,
    forecast_chart_data: pd.DataFrame,
    purchase_plan: pd.DataFrame,
    top_risks: pd.DataFrame,
    reliability_distribution: pd.DataFrame,
    analysis_reliability: dict[str, Any],
    abc_distribution: pd.DataFrame,
    abc_xyz_matrix: list[dict[str, Any]],
    data_quality: dict[str, Any],
    source_worksheet,
    source_sheet_name: str,
) -> None:
    worksheet.hide_gridlines(2)
    worksheet.activate()
    worksheet.set_first_sheet()
    worksheet.set_selection(0, 0, 0, 0)
    worksheet.set_tab_color("#2563EB")
    worksheet.set_zoom(115)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 1)
    worksheet.repeat_rows(0, 0)
    worksheet.print_area("A1:Z122")
    worksheet.set_default_row(18, hide_unused_rows=True)
    worksheet.set_column("A:Z", 11.25, formats["dashboard_canvas"])
    worksheet.set_column("AA:XFD", 3, None, {"hidden": True})
    for row_index in range(0, 122):
        worksheet.set_row(row_index, 21)
    for row_index in range(0, 7):
        worksheet.set_row(row_index, 26)
    for row_index in range(8, 15):
        worksheet.set_row(row_index, 28)
    for row_index in range(16, 28):
        worksheet.set_row(row_index, 25)
    for row_index in range(29, 44):
        worksheet.set_row(row_index, 24)
    for row_index in range(46, 122):
        worksheet.set_row(row_index, 24)
    worksheet.write_blank(121, 25, None, formats["dashboard_canvas"])

    _paint_card_area(worksheet, 0, 5, 0, 25, formats["dashboard_header_bg"])
    worksheet.merge_range("A1:L3", "StockPilot AI", formats["dashboard_title"])
    worksheet.merge_range("A4:L6", "Управленческий отчёт по продажам, запасам и закупкам", formats["dashboard_subtitle"])
    _write_dashboard_meta_grid(worksheet, meta, formats)
    _paint_card_area(worksheet, 7, 13, 0, 25, formats["dashboard_panel"])
    worksheet.merge_range(
        "A8:Z14",
        _build_executive_conclusion(
            summary_metrics=summary_metrics,
            product_sales=product_sales,
            purchase_plan=purchase_plan,
            analysis_reliability=analysis_reliability,
        ),
        formats["executive_box"],
    )

    category_chart_df = _prepare_dashboard_value_chart_data(category_sales, "category", "total_revenue", "Категория", "Выручка", 6)
    product_chart_df = _prepare_dashboard_value_chart_data(product_sales, "product_name", "total_revenue", "Товар", "Выручка", 6)
    daily_sales_chart_df = _prepare_daily_sales_chart_data(daily_sales)
    priority_distribution = _build_priority_distribution_df(purchase_plan)
    dashboard_sources = {
        "category_revenue": category_chart_df,
        "top_products": product_chart_df,
        "daily_sales": daily_sales_chart_df,
        "forecast": forecast_chart_data,
        "priority": priority_distribution,
        "reliability": reliability_distribution,
        "abc": abc_distribution,
    }
    source_ranges = _write_dashboard_chart_sources(
        worksheet=source_worksheet,
        formats=formats,
        sources=dashboard_sources,
    )

    kpis = [
        ("Выручка", summary_metrics.get("total_revenue", 0), "money", "Фактическая выручка"),
        ("Продано единиц", summary_metrics.get("total_units_sold", 0), "integer", "Объём продаж"),
        ("SKU в анализе", summary_metrics.get("unique_products", 0), "integer", "Товары в расчёте"),
        ("К закупке", purchase_plan["Итоговое количество"].sum() if not purchase_plan.empty else 0, "integer", "Итоговый заказ"),
        ("Риск дефицита", _count_priority(purchase_plan), "integer", "Высокий приоритет"),
        ("Избыток", _count_overstock(purchase_plan), "integer", "Требует проверки"),
        ("Качество данных", _normalize_percent_for_excel(data_quality.get("completeness_score")) if data_quality else None, "ratio", "Полнота файла"),
        (
            "Надёжность прогноза",
            localize_forecast_confidence((analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence")),
            "text",
            "Без обещаний точности",
        ),
    ]
    kpi_cells = ["A17", "H17", "O17", "V17", "A23", "H23", "O23", "V23"]
    for (label, value, style, note), cell in zip(kpis, kpi_cells):
        _write_dashboard_kpi_card(worksheet, cell, label, value, style, note, formats)

    _paint_card_area(worksheet, 28, 43, 0, 12, formats["dashboard_panel"])
    _write_action_panel(
        worksheet,
        cell="A30",
        end_col=12,
        title="Что сделать сегодня",
        items=_build_next_actions(purchase_plan, analysis_reliability),
        formats=formats,
    )
    _paint_card_area(worksheet, 28, 43, 13, 25, formats["dashboard_panel"])
    _write_action_panel(
        worksheet,
        cell="N30",
        end_col=25,
        title="Что проверить вручную",
        items=_build_manual_checks(analysis_reliability, data_quality),
        formats=formats,
    )

    _paint_card_area(worksheet, 46, 69, 0, 12, formats["dashboard_panel"])
    _paint_card_area(worksheet, 46, 69, 13, 25, formats["dashboard_panel"])
    _paint_card_area(worksheet, 72, 95, 0, 12, formats["dashboard_panel"])
    _paint_card_area(worksheet, 72, 95, 13, 25, formats["dashboard_panel"])
    _paint_card_area(worksheet, 98, 121, 0, 25, formats["dashboard_panel"])
    worksheet.merge_range("A47:M47", "Продажи и выручка", formats["section_title"])
    worksheet.merge_range("N47:Z47", "Прогноз и надёжность", formats["section_title"])
    worksheet.merge_range("A73:M73", "Закупочный план", formats["section_title"])
    worksheet.merge_range("N73:Z73", "Риски", formats["section_title"])
    worksheet.merge_range("A99:Z99", "ABC/XYZ", formats["section_title"])
    _insert_dashboard_charts(
        workbook=workbook,
        worksheet=worksheet,
        source_sheet_name=source_sheet_name,
        source_ranges=source_ranges,
        formats=formats,
    )
    _write_dashboard_insight(
        worksheet,
        cell="A70",
        end_col=12,
        text=_build_revenue_insight(category_chart_df),
        formats=formats,
    )
    _write_dashboard_insight(
        worksheet,
        cell="N70",
        end_col=25,
        text=_build_reliability_insight(analysis_reliability),
        formats=formats,
    )
    _write_dashboard_heatmap_block(
        worksheet=worksheet,
        cell="N100",
        title="ABC/XYZ матрица",
        subtitle="Матрица классов по выручке и стабильности спроса",
        matrix=_build_abc_xyz_heatmap(abc_xyz_matrix),
        summary_rows=_build_dashboard_rows(abc_distribution, [("Класс", "text"), ("SKU", "integer")], 6),
        formats=formats,
    )
    _write_risk_panel(worksheet, cell="N75", end_col=25, risks=top_risks, formats=formats)
    _write_purchase_mini_list(worksheet, cell="A88", end_col=12, purchase_plan=purchase_plan, formats=formats)


def _write_summary_sheet(
    *,
    worksheet,
    formats: dict[str, Any],
    meta: dict[str, Any],
    summary_metrics: dict[str, Any],
    product_sales: pd.DataFrame,
    purchase_plan: pd.DataFrame,
    recommendations: pd.DataFrame | None,
    top_risks: pd.DataFrame,
    analysis_reliability: dict[str, Any],
    data_quality: dict[str, Any],
) -> None:
    worksheet.hide_gridlines(2)
    worksheet.activate()
    worksheet.set_first_sheet()
    worksheet.set_selection(0, 0, 0, 0)
    worksheet.set_zoom(100)
    worksheet.set_column("A:A", 2)
    worksheet.set_column("B:B", 22)
    worksheet.set_column("C:H", 15)
    worksheet.set_column("I:I", 18)
    worksheet.set_column("J:N", 18)
    worksheet.set_column("O:Z", 14, None, {"hidden": True})

    worksheet.merge_range("B2:H3", "StockPilot AI", formats["hero_title"])
    worksheet.merge_range("B4:H4", "Управленческий отчёт по продажам, запасам и закупкам", formats["hero_subtitle"])
    worksheet.write("J2", "Дата анализа", formats["meta_label"])
    worksheet.write("K2", meta["generated_at"], formats["meta_value"])
    worksheet.write("J3", "Файл", formats["meta_label"])
    worksheet.write("K3", meta["source_filename"], formats["meta_value"])
    worksheet.write("J4", "Период", formats["meta_label"])
    worksheet.write("K4", meta["period"], formats["meta_value"])
    worksheet.write("J5", "SKU / строк", formats["meta_label"])
    worksheet.write("K5", f"{meta['sku_count']} / {meta['row_count']}", formats["meta_value"])
    worksheet.write("J6", "Горизонт", formats["meta_label"])
    worksheet.write("K6", f"{meta['horizon']} дн.", formats["meta_value"])

    worksheet.merge_range(
        "B7:N8",
        _build_executive_conclusion(
            summary_metrics=summary_metrics,
            product_sales=product_sales,
            purchase_plan=purchase_plan,
            analysis_reliability=analysis_reliability,
        ),
        formats["executive_box"],
    )

    overstock_count = 0
    if recommendations is not None and not recommendations.empty and "overstock_risk" in recommendations.columns:
        overstock_count = int(pd.to_numeric(recommendations["overstock_risk"], errors="coerce").fillna(0).ge(0.55).sum())
    kpis = [
        ("Выручка", summary_metrics.get("total_revenue", 0), "money"),
        ("Продано единиц", summary_metrics.get("total_units_sold", 0), "integer"),
        ("SKU в анализе", summary_metrics.get("unique_products", 0), "integer"),
        ("К закупке", purchase_plan["Итоговое количество"].sum() if not purchase_plan.empty else 0, "integer"),
        ("Риск дефицита", _count_priority(purchase_plan), "integer"),
        ("Избыток", overstock_count, "integer"),
        ("Качество данных", _normalize_percent_for_excel(data_quality.get("completeness_score")) if data_quality else None, "ratio"),
        ("Надёжность", _format_reliability_label(analysis_reliability), "text"),
    ]
    positions = ["B10", "D10", "F10", "H10", "J10", "L10", "B14", "D14"]
    for (label, value, style), cell in zip(kpis, positions):
        _write_kpi_card(worksheet, cell, label, value, style, formats)

    worksheet.write("B18", "Что сделать в первую очередь", formats["section_title"])
    next_actions = _build_next_actions(purchase_plan, analysis_reliability)
    for index, action in enumerate(next_actions[:4], start=19):
        worksheet.write(f"B{index}", f"{index - 18}.", formats["list_index"])
        worksheet.merge_range(f"C{index}:H{index}", action, formats["list_text"])

    worksheet.write("J18", "Что проверить вручную", formats["section_title"])
    for index, action in enumerate(_build_manual_checks(analysis_reliability, data_quality)[:4], start=19):
        worksheet.write(f"J{index}", f"{index - 18}.", formats["list_index"])
        worksheet.merge_range(f"K{index}:N{index}", action, formats["list_text"])

    worksheet.write("B25", "Топ-5 закупочных рекомендаций", formats["section_title"])
    _write_small_table(
        worksheet,
        start_row=25,
        start_col=1,
        df=(purchase_plan[purchase_plan["Итоговое количество"] > 0].head(5) if not purchase_plan.empty else purchase_plan),
        formats=formats,
    )

    worksheet.write("J25", "Топ-5 рисков", formats["section_title"])
    _write_small_table(
        worksheet,
        start_row=25,
        start_col=9,
        df=top_risks.head(5),
        formats=formats,
    )

    worksheet.write("B34", "Надёжность прогноза", formats["section_title"])
    reliability = analysis_reliability.get("forecast_quality", {}) or {}
    reliability_rows = [
        ("Уровень", localize_value(reliability.get("overall_confidence")) or "Нет данных"),
        ("WAPE", _format_ratio_text(reliability.get("wape"))),
        ("MAE", _format_decimal_text(reliability.get("mae"))),
        ("Bias", _format_ratio_text(reliability.get("bias"))),
    ]
    row = 35
    for label, value in reliability_rows:
        worksheet.write(f"B{row}", label, formats["meta_label"])
        worksheet.write(f"C{row}", value, formats["meta_value"])
        row += 1


def _write_chart_sources(
    *,
    worksheet,
    formats: dict[str, Any],
    category_chart_data: pd.DataFrame,
    top_products_chart_data: pd.DataFrame,
    forecast_chart_data: pd.DataFrame,
    reliability_distribution: pd.DataFrame,
    abc_distribution: pd.DataFrame,
) -> None:
    worksheet.hide()
    worksheet.hide_gridlines(2)
    start_col = 14
    blocks = [
        ("category", category_chart_data),
        ("products", top_products_chart_data),
        ("forecast", forecast_chart_data),
        ("reliability", reliability_distribution),
        ("abc", abc_distribution),
    ]
    current_row = 1
    for name, df in blocks:
        worksheet.write(current_row, start_col, name)
        if df.empty:
            current_row += 4
            continue
        for col_index, column in enumerate(df.columns):
            worksheet.write(current_row, start_col + col_index, column)
        for row_index, (_, values) in enumerate(df.iterrows(), start=1):
            for col_index, value in enumerate(values):
                if isinstance(value, pd.Timestamp):
                    worksheet.write_datetime(current_row + row_index, start_col + col_index, value.to_pydatetime(), formats["date"])
                else:
                    worksheet.write(current_row + row_index, start_col + col_index, value)
        current_row += len(df) + 3


def _insert_summary_charts(*, workbook, worksheet, chart_sources: dict[str, pd.DataFrame], source_sheet_name: str) -> None:
    source = source_sheet_name
    source_map = {}
    row = 1
    col = 14
    for key, df in chart_sources.items():
        source_map[key] = (row, len(df))
        row += len(df) + 3

    if not chart_sources["category"].empty:
        chart = workbook.add_chart({"type": "column"})
        start_row, length = source_map["category"]
        chart.add_series(
            {
                "name": "Выручка по категориям",
                "categories": [source, start_row + 1, col, start_row + length, col],
                "values": [source, start_row + 1, col + 1, start_row + length, col + 1],
                "fill": {"color": "#2563EB"},
                "border": {"none": True},
            }
        )
        chart.set_title({"name": "Выручка по категориям"})
        chart.set_legend({"none": True})
        chart.set_style(10)
        chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
        chart.set_plotarea({"border": {"color": "#E8EEF6"}, "fill": {"color": "#FBFCFE"}})
        worksheet.insert_chart("B42", chart, {"x_scale": 1.15, "y_scale": 0.95, "object_position": 2})

    if not chart_sources["products"].empty:
        chart = workbook.add_chart({"type": "bar"})
        start_row, length = source_map["products"]
        chart.add_series(
            {
                "name": "Топ товаров",
                "categories": [source, start_row + 1, col, start_row + length, col],
                "values": [source, start_row + 1, col + 1, start_row + length, col + 1],
                "fill": {"color": "#0F766E"},
                "border": {"none": True},
            }
        )
        chart.set_title({"name": "Топ товаров по выручке"})
        chart.set_legend({"none": True})
        chart.set_style(10)
        chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
        chart.set_plotarea({"border": {"color": "#E8EEF6"}, "fill": {"color": "#FBFCFE"}})
        worksheet.insert_chart("I42", chart, {"x_scale": 1.15, "y_scale": 0.95, "object_position": 2})

    if not chart_sources["forecast"].empty:
        chart = workbook.add_chart({"type": "line"})
        start_row, length = source_map["forecast"]
        chart.add_series(
            {
                "name": "Прогноз спроса",
                "categories": [source, start_row + 1, col, start_row + length, col],
                "values": [source, start_row + 1, col + 1, start_row + length, col + 1],
                "line": {"color": "#7C3AED", "width": 2.25},
            }
        )
        chart.set_title({"name": "Прогноз спроса по дням"})
        chart.set_legend({"none": True})
        chart.set_x_axis({"date_axis": True, "num_format": "dd.mm"})
        chart.set_style(10)
        chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
        chart.set_plotarea({"border": {"color": "#E8EEF6"}, "fill": {"color": "#FBFCFE"}})
        worksheet.insert_chart("B58", chart, {"x_scale": 1.25, "y_scale": 0.95, "object_position": 2})


def _create_formats(workbook) -> dict[str, Any]:
    return {
        "dashboard_canvas": workbook.add_format({"fg_color": "#F3F6FB"}),
        "dashboard_header_bg": workbook.add_format({"fg_color": "#EEF4FF", "border": 1, "border_color": "#D8E0EA"}),
        "dashboard_panel": workbook.add_format({"fg_color": "#FFFFFF"}),
        "dashboard_panel_soft": workbook.add_format({"fg_color": "#FFFFFF"}),
        "dashboard_title": workbook.add_format({"bold": True, "font_size": 30, "font_color": "#0F172A", "valign": "vcenter"}),
        "dashboard_subtitle": workbook.add_format({"font_size": 14, "font_color": "#475569", "text_wrap": True, "valign": "top"}),
        "dashboard_subnote": workbook.add_format({"font_size": 9, "font_color": "#64748B"}),
        "hero_title": workbook.add_format({"bold": True, "font_size": 22, "font_color": "#0F172A"}),
        "hero_subtitle": workbook.add_format({"font_size": 11, "font_color": "#475569"}),
        "meta_label": workbook.add_format({"font_size": 10, "font_color": "#64748B", "bold": True}),
        "meta_value": workbook.add_format({"font_size": 10, "font_color": "#0F172A"}),
        "meta_value_wrap": workbook.add_format({"font_size": 10, "font_color": "#0F172A", "text_wrap": True, "shrink": True}),
        "dashboard_meta_label": workbook.add_format(
            {
                "font_size": 8,
                "font_color": "#64748B",
                "bold": True,
                "fg_color": "#F8FAFC",
                "top": 1,
                "left": 1,
                "right": 1,
                "border_color": "#D8E0EA",
            }
        ),
        "dashboard_meta_value": workbook.add_format(
            {
                "font_size": 10,
                "font_color": "#0F172A",
                "bold": True,
                "text_wrap": True,
                "shrink": True,
                "valign": "top",
                "fg_color": "#F8FAFC",
                "bottom": 1,
                "left": 1,
                "right": 1,
                "border_color": "#D8E0EA",
            }
        ),
        "executive_box": workbook.add_format(
            {
                "bold": True,
                "font_size": 15,
                "font_color": "#0F172A",
                "text_wrap": True,
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
                "border": 1,
                "border_color": "#BFDBFE",
                "left": 1,
                "left_color": "#BFDBFE",
            }
        ),
        "dashboard_kpi_label": workbook.add_format(
            {
                "font_size": 10,
                "font_color": "#64748B",
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "dashboard_kpi_value_money": workbook.add_format(
            {
                "font_size": 22,
                "bold": True,
                "font_color": "#0F172A",
                "num_format": '#,##0 "₽"',
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "dashboard_kpi_value_integer": workbook.add_format(
            {
                "font_size": 22,
                "bold": True,
                "font_color": "#0F172A",
                "num_format": "#,##0",
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "dashboard_kpi_value_ratio": workbook.add_format(
            {
                "font_size": 22,
                "bold": True,
                "font_color": "#0F172A",
                "num_format": "0.0%",
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "dashboard_kpi_value_text": workbook.add_format(
            {
                "font_size": 20,
                "bold": True,
                "font_color": "#0F172A",
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "dashboard_kpi_note": workbook.add_format(
            {
                "font_size": 9,
                "font_color": "#64748B",
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#FFFFFF",
            }
        ),
        "card_label": workbook.add_format({"font_size": 9, "font_color": "#64748B", "align": "center"}),
        "card_value_money": workbook.add_format({"font_size": 16, "bold": True, "num_format": '#,##0 "₽"', "align": "center"}),
        "card_value_integer": workbook.add_format({"font_size": 16, "bold": True, "num_format": "#,##0", "align": "center"}),
        "card_value_ratio": workbook.add_format({"font_size": 16, "bold": True, "num_format": "0.0%", "align": "center"}),
        "card_value_text": workbook.add_format({"font_size": 13, "bold": True, "font_color": "#0F172A", "align": "center"}),
        "card_note": workbook.add_format({"font_size": 9, "font_color": "#475569", "align": "center"}),
        "card_box": workbook.add_format({"border": 1, "border_color": "#E2E8F0", "fg_color": "#FFFFFF"}),
        "section_title": workbook.add_format({"bold": True, "font_size": 13, "font_color": "#0F172A"}),
        "soft_box": workbook.add_format({"border": 1, "border_color": "#E2E8F0", "fg_color": "#FFFFFF"}),
        "list_index": workbook.add_format({"bold": True, "font_color": "#2563EB"}),
        "list_text": workbook.add_format({"text_wrap": True, "font_color": "#0F172A"}),
        "action_panel_bg": workbook.add_format({"fg_color": "#FFFFFF", "border": 1, "border_color": "#E2E8F0"}),
        "action_index": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "fg_color": "#2563EB",
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "action_text": workbook.add_format(
            {
                "text_wrap": True,
                "font_size": 11,
                "font_color": "#0F172A",
                "valign": "vcenter",
                "fg_color": "#F8FAFC",
            }
        ),
        "chart_placeholder": workbook.add_format(
            {
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#F8FAFC",
                "font_color": "#64748B",
                "border": 1,
                "border_color": "#D8E0EA",
            }
        ),
        "table_header": workbook.add_format(
            {"bold": True, "font_color": "#FFFFFF", "fg_color": "#0F172A", "border": 1, "border_color": "#0F172A", "align": "center", "valign": "vcenter"}
        ),
        "text": workbook.add_format({"text_wrap": True, "valign": "top"}),
        "money": workbook.add_format({"num_format": '#,##0 "₽"'}),
        "integer": workbook.add_format({"num_format": "#,##0"}),
        "decimal": workbook.add_format({"num_format": "#,##0.0"}),
        "ratio": workbook.add_format({"num_format": "0.0%"}),
        "date": workbook.add_format({"num_format": "dd.mm.yyyy"}),
        "priority_high": workbook.add_format({"fg_color": "#FEF3C7", "font_color": "#92400E"}),
        "priority_critical": workbook.add_format({"fg_color": "#FEE2E2", "font_color": "#991B1B"}),
        "priority_medium": workbook.add_format({"fg_color": "#DBEAFE", "font_color": "#1D4ED8"}),
        "priority_low": workbook.add_format({"fg_color": "#E2E8F0", "font_color": "#334155"}),
        "status_done": workbook.add_format({"fg_color": "#DCFCE7", "font_color": "#166534"}),
        "status_in_purchase": workbook.add_format({"fg_color": "#E0F2FE", "font_color": "#075985"}),
        "status_new": workbook.add_format({"fg_color": "#F8FAFC", "font_color": "#334155"}),
        "heat_high": workbook.add_format({"fg_color": "#FED7AA", "font_color": "#9A3412", "align": "center"}),
        "heat_medium": workbook.add_format({"fg_color": "#FEF3C7", "font_color": "#92400E", "align": "center"}),
        "heat_low": workbook.add_format({"fg_color": "#F8FAFC", "font_color": "#475569", "align": "center"}),
    }


def _write_kpi_card(worksheet, cell: str, label: str, value: Any, style: str, formats: dict[str, Any]) -> None:
    row = int(cell[1:])
    col = ord(cell[0]) - ord("A")
    fmt = formats["card_value_integer"]
    if style == "money":
        fmt = formats["card_value_money"]
    elif style == "ratio":
        fmt = formats["card_value_ratio"]
        if value is not None:
            value = _normalize_percent_for_excel(value)
    elif style == "text":
        fmt = formats["card_value_text"]
    worksheet.merge_range(row - 1, col, row - 1, col + 1, label, formats["card_label"])
    worksheet.merge_range(row, col, row, col + 1, 0 if value is None else value, fmt)


def _write_dashboard_kpi_card(
    worksheet,
    cell: str,
    label: str,
    value: Any,
    style: str,
    note: str,
    formats: dict[str, Any],
) -> None:
    row = int(cell[1:]) - 1
    col = ord(cell[0]) - ord("A")
    end_col = min(col + 5, 25)
    _paint_card_area(worksheet, row, row + 4, col, end_col, formats["dashboard_panel_soft"])
    value_format = formats["dashboard_kpi_value_integer"]
    display_value = value
    if style == "money":
        value_format = formats["dashboard_kpi_value_money"]
    elif style == "ratio":
        value_format = formats["dashboard_kpi_value_ratio"]
        if value is not None:
            display_value = _normalize_percent_for_excel(value)
    elif style == "text":
        value_format = formats["dashboard_kpi_value_text"]
        display_value = str(value or "Нет данных").capitalize()
    worksheet.merge_range(row, col, row, end_col, label, formats["dashboard_kpi_label"])
    worksheet.merge_range(row + 1, col, row + 3, end_col, 0 if display_value is None else display_value, value_format)
    worksheet.merge_range(row + 4, col, row + 4, end_col, note, formats["dashboard_kpi_note"])


def _paint_card_area(worksheet, first_row: int, last_row: int, first_col: int, last_col: int, cell_format) -> None:
    for row in range(first_row, last_row + 1):
        for col in range(first_col, last_col + 1):
            worksheet.write_blank(row, col, None, cell_format)


def _write_dashboard_meta_grid(worksheet, meta: dict[str, Any], formats: dict[str, Any]) -> None:
    _write_meta_card(worksheet, 0, 13, 1, 25, "Файл", meta["source_filename"], formats)
    _write_meta_card(worksheet, 2, 13, 3, 18, "Дата анализа", meta["generated_at"], formats)
    _write_meta_card(worksheet, 2, 20, 3, 25, "Период", meta["period"], formats)
    _write_meta_card(worksheet, 4, 13, 5, 18, "SKU / строк", f"{meta['sku_count']} / {meta['row_count']}", formats)
    _write_meta_card(worksheet, 4, 20, 5, 25, "Горизонт прогноза", f"{meta['horizon']} дн.", formats)


def _write_meta_card(
    worksheet,
    first_row: int,
    first_col: int,
    last_row: int,
    last_col: int,
    label: str,
    value: Any,
    formats: dict[str, Any],
) -> None:
    worksheet.merge_range(first_row, first_col, first_row, last_col, label, formats["dashboard_meta_label"])
    worksheet.merge_range(first_row + 1, first_col, last_row, last_col, value, formats["dashboard_meta_value"])


def _write_action_panel(
    worksheet,
    *,
    cell: str,
    end_col: int,
    title: str,
    items: list[str],
    formats: dict[str, Any],
) -> None:
    start_row, start_col = _cell_to_row_col(cell)
    worksheet.merge_range(start_row, start_col, start_row, end_col, title, formats["section_title"])
    item_row = start_row + 2
    for index, item in enumerate(items[:5], start=1):
        worksheet.merge_range(item_row, start_col, item_row + 1, start_col, index, formats["action_index"])
        worksheet.merge_range(item_row, start_col + 1, item_row + 1, end_col, item, formats["action_text"])
        item_row += 2


def _write_dashboard_insight(worksheet, *, cell: str, end_col: int, text: str, formats: dict[str, Any]) -> None:
    start_row, start_col = _cell_to_row_col(cell)
    worksheet.merge_range(start_row, start_col, start_row + 1, end_col, text, formats["dashboard_subnote"])


def _write_risk_panel(worksheet, *, cell: str, end_col: int, risks: pd.DataFrame, formats: dict[str, Any]) -> None:
    start_row, start_col = _cell_to_row_col(cell)
    if risks is None or risks.empty:
        worksheet.merge_range(start_row, start_col, start_row + 2, end_col, "Критичных рисков не найдено.", formats["action_text"])
        return
    row = start_row
    for index, (_, item) in enumerate(risks.head(5).iterrows(), start=1):
        sku = str(item.get("SKU", "SKU"))
        risk = item.get("Риск", "")
        action = str(item.get("Действие", "Проверьте остаток и спрос вручную."))
        text = f"{sku}: риск {_format_ratio_text(risk)}. {action}"
        worksheet.merge_range(row, start_col, row + 1, start_col, index, formats["action_index"])
        worksheet.merge_range(row, start_col + 1, row + 1, end_col, text, formats["action_text"])
        row += 3


def _write_purchase_mini_list(
    worksheet,
    *,
    cell: str,
    end_col: int,
    purchase_plan: pd.DataFrame,
    formats: dict[str, Any],
) -> None:
    start_row, start_col = _cell_to_row_col(cell)
    worksheet.merge_range(start_row, start_col, start_row, end_col, "Топ позиций к заказу", formats["section_title"])
    if purchase_plan is None or purchase_plan.empty:
        worksheet.merge_range(start_row + 2, start_col, start_row + 4, end_col, "Нет активных закупочных позиций.", formats["action_text"])
        return
    rows = purchase_plan[purchase_plan["Итоговое количество"] > 0].head(4)
    if rows.empty:
        worksheet.merge_range(start_row + 2, start_col, start_row + 4, end_col, "Активная закупка не требуется.", formats["action_text"])
        return
    row = start_row + 2
    for index, (_, item) in enumerate(rows.iterrows(), start=1):
        sku = str(item.get("SKU", "SKU"))
        product = str(item.get("Товар", "Товар"))
        qty = format_integer_text(item.get("Итоговое количество"))
        reason = str(item.get("Причина", "Проверьте покрытие и спрос."))
        worksheet.merge_range(row, start_col, row + 1, start_col, index, formats["action_index"])
        worksheet.merge_range(row, start_col + 1, row + 1, end_col, f"{sku} — {product}: к заказу {qty} ед. {reason}", formats["action_text"])
        row += 2


def _cell_to_row_col(cell: str) -> tuple[int, int]:
    letters = "".join(ch for ch in cell if ch.isalpha()).upper()
    digits = "".join(ch for ch in cell if ch.isdigit())
    col = 0
    for letter in letters:
        col = col * 26 + ord(letter) - ord("A") + 1
    return int(digits) - 1, col - 1


def _write_dashboard_chart_sources(
    *,
    worksheet,
    formats: dict[str, Any],
    sources: dict[str, pd.DataFrame],
) -> dict[str, dict[str, int]]:
    worksheet.hide()
    worksheet.hide_gridlines(2)
    worksheet.set_column(0, 3, 24)
    ranges: dict[str, dict[str, int]] = {}
    current_row = 0
    for key, df in sources.items():
        prepared = df.copy() if df is not None else pd.DataFrame()
        worksheet.write(current_row, 0, key, formats["meta_label"])
        header_row = current_row + 1
        if prepared.empty:
            ranges[key] = {"first_row": header_row + 1, "last_row": header_row, "label_col": 0, "value_col": 1}
            current_row += 4
            continue
        for col_index, column in enumerate(prepared.columns[:2]):
            worksheet.write(header_row, col_index, column, formats["table_header"])
        first_row = header_row + 1
        for row_offset, (_, record) in enumerate(prepared.iloc[:, :2].iterrows()):
            for col_index, value in enumerate(record):
                target_row = first_row + row_offset
                if isinstance(value, pd.Timestamp):
                    worksheet.write_datetime(target_row, col_index, value.to_pydatetime(), formats["date"])
                else:
                    worksheet.write(target_row, col_index, value)
        last_row = first_row + len(prepared) - 1
        ranges[key] = {"first_row": first_row, "last_row": last_row, "label_col": 0, "value_col": 1}
        current_row = last_row + 3
    return ranges


def _insert_dashboard_charts(
    *,
    workbook,
    worksheet,
    source_sheet_name: str,
    source_ranges: dict[str, dict[str, int]],
    formats: dict[str, Any],
) -> None:
    charts = [
        ("category_revenue", "column", "Выручка по категориям", "A49", "#2563EB", False, 650, 220),
        ("top_products", "bar", "Топ SKU по выручке", "A60", "#0F766E", False, 650, 220),
        ("forecast", "line", "Прогноз спроса по дням", "N49", "#7C3AED", True, 650, 220),
        ("reliability", "doughnut", "Надёжность SKU", "N60", "#7C3AED", False, 620, 220),
        ("priority", "column", "Закупка по приоритетам", "A75", "#DC2626", False, 650, 260),
        ("abc", "column", "ABC/XYZ распределение", "A100", "#F59E0B", False, 650, 320),
    ]
    for key, chart_type, title, cell, color, date_axis, width, height in charts:
        chart_range = source_ranges.get(key)
        if not chart_range or chart_range["last_row"] < chart_range["first_row"]:
            _write_chart_placeholder(worksheet, cell, title, formats)
            continue
        chart = workbook.add_chart({"type": chart_type})
        series: dict[str, Any] = {
            "name": title,
            "categories": [
                source_sheet_name,
                chart_range["first_row"],
                chart_range["label_col"],
                chart_range["last_row"],
                chart_range["label_col"],
            ],
            "values": [
                source_sheet_name,
                chart_range["first_row"],
                chart_range["value_col"],
                chart_range["last_row"],
                chart_range["value_col"],
            ],
        }
        if chart_type in {"column", "bar"}:
            series["fill"] = {"color": color}
            series["border"] = {"none": True}
        elif chart_type == "line":
            series["line"] = {"color": color, "width": 2.25}
            series["marker"] = {"type": "circle", "size": 4, "border": {"color": color}, "fill": {"color": color}}
        chart.add_series(series)
        chart.set_title({"name": title, "name_font": {"size": 13, "bold": True, "color": "#0F172A"}})
        chart.set_chartarea({"border": {"none": True}, "fill": {"color": "#FFFFFF"}})
        chart.set_plotarea({"border": {"color": "#E8EEF6"}, "fill": {"color": "#FBFCFE"}})
        chart.set_style(10)
        chart.set_size({"width": width, "height": height})
        if chart_type == "doughnut":
            chart.set_hole_size(58)
            chart.set_legend({"position": "bottom", "font": {"size": 9, "color": "#64748B"}})
        else:
            chart.set_legend({"none": True})
            x_axis = {
                "num_font": {"size": 9, "color": "#64748B"},
                "major_gridlines": {"visible": False},
            }
            if date_axis:
                x_axis["date_axis"] = True
                x_axis["num_format"] = "dd.mm"
            chart.set_x_axis(x_axis)
            chart.set_y_axis(
                {
                    "num_font": {"size": 9, "color": "#64748B"},
                    "major_gridlines": {"visible": True, "line": {"color": "#E2E8F0", "width": 0.75}},
                }
            )
        worksheet.insert_chart(cell, chart, {"object_position": 2})


def _write_chart_placeholder(worksheet, cell: str, title: str, formats: dict[str, Any]) -> None:
    row = int(cell[1:]) - 1
    col = ord(cell[0]) - ord("A")
    worksheet.merge_range(row, col, row + 8, col + 4, f"{title}\nНет данных для графика", formats["chart_placeholder"])


def _write_meta_panel(worksheet, cell: str, meta: dict[str, Any], formats: dict[str, Any]) -> None:
    start_row = int(cell[1:]) - 1
    start_col = ord(cell[0]) - ord("A")
    rows = [
        ("Файл", meta["source_filename"]),
        ("Дата анализа", meta["generated_at"]),
        ("Период", meta["period"]),
        ("SKU / строк", f"{meta['sku_count']} / {meta['row_count']}"),
        ("Горизонт прогноза", f"{meta['horizon']} дн."),
    ]
    for offset, (label, value) in enumerate(rows):
        worksheet.write(start_row + offset, start_col, label, formats["meta_label"])
        worksheet.merge_range(start_row + offset, start_col + 1, start_row + offset, start_col + 4, value, formats["meta_value_wrap"])


def _write_bullet_box(
    worksheet,
    *,
    start_row: int,
    start_col: int,
    end_col: int,
    items: list[str],
    formats: dict[str, Any],
) -> None:
    body_start = start_row + 1
    body_end = start_row + 7
    for row_index in range(body_start, body_end + 1):
        for col_index in range(start_col, end_col + 1):
            worksheet.write_blank(row_index, col_index, None, formats["soft_box"])
    row = body_start
    for index, item in enumerate(items[:5], start=1):
        worksheet.write(row, start_col, f"{index}.", formats["list_index"])
        worksheet.merge_range(row, start_col + 1, row, end_col - 1, item, formats["list_text"])
        row += 1


def _write_small_table(worksheet, *, start_row: int, start_col: int, df: pd.DataFrame, formats: dict[str, Any]) -> None:
    if df is None or df.empty:
        worksheet.write(start_row + 1, start_col, "Нет данных", formats["meta_value"])
        return
    for col_offset, column in enumerate(df.columns[:5]):
        worksheet.write(start_row + 1, start_col + col_offset, column, formats["table_header"])
    for row_offset, (_, values) in enumerate(df.iloc[:, :5].iterrows(), start=2):
        for col_offset, (column, value) in enumerate(zip(df.columns[:5], values)):
            cell_format = formats["text"]
            if isinstance(value, (int, float)):
                if "Риск" in str(column) or "%" in str(column):
                    cell_format = formats["ratio"]
                    value = float(value) if abs(float(value)) <= 1 else float(value) / 100
                elif "Покрытие" in str(column) or "WAPE" in str(column) or "Bias" in str(column):
                    cell_format = formats["decimal"]
                else:
                    cell_format = formats["integer"]
            worksheet.write(start_row + row_offset, start_col + col_offset, value, cell_format)


def _format_sheet_base(worksheet, formats: dict[str, Any]) -> None:
    safe_freeze_panes(worksheet, 1, 0)
    worksheet.set_row(0, 24, formats["table_header"])
    worksheet.autofilter(0, 0, max(1, worksheet.dim_rowmax), max(1, worksheet.dim_colmax))


def _format_dashboard_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.hide_gridlines(2)


def _format_purchase_plan_sheet(worksheet, formats: dict[str, Any]) -> None:
    widths = [14, 32, 20, 22, 14, 12, 14, 16, 18, 18, 18, 40, 16, 28]
    for index, width in enumerate(widths):
        worksheet.set_column(index, index, width, formats["text"] if index in {1, 11, 13} else None)
    worksheet.conditional_format("E2:E1000", {"type": "text", "criteria": "containing", "value": "Высокий", "format": formats["priority_high"]})
    worksheet.conditional_format("E2:E1000", {"type": "text", "criteria": "containing", "value": "Критический", "format": formats["priority_critical"]})
    worksheet.conditional_format("M2:M1000", {"type": "text", "criteria": "containing", "value": "Выполнено", "format": formats["status_done"]})
    worksheet.conditional_format("M2:M1000", {"type": "text", "criteria": "containing", "value": "В закупке", "format": formats["status_in_purchase"]})
    worksheet.conditional_format("M2:M1000", {"type": "text", "criteria": "containing", "value": "Новая", "format": formats["status_new"]})


def _format_reliability_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 34, formats["text"])
    worksheet.set_column(1, 1, 18, formats["text"])


def _format_data_quality_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 32, formats["text"])
    worksheet.set_column(1, 1, 18)


def _format_insights_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 8)
    worksheet.set_column(1, 1, 96, formats["text"])


def _format_risks_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 14)
    worksheet.set_column(1, 1, 30, formats["text"])
    worksheet.set_column(2, 3, 18)
    worksheet.set_column(4, 4, 44, formats["text"])


def _format_product_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 14)
    worksheet.set_column(1, 1, 32, formats["text"])
    worksheet.set_column(2, 2, 20)
    worksheet.set_column(3, 9, 16)


def _format_forecast_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 14)
    worksheet.set_column(1, 1, 30, formats["text"])
    worksheet.set_column(2, 2, 18)
    worksheet.set_column(3, 12, 16)


def _format_abc_xyz_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 14)
    worksheet.set_column(1, 1, 30, formats["text"])
    worksheet.set_column(2, 2, 18)
    worksheet.set_column(3, 5, 12)
    worksheet.set_column(6, 6, 18)
    worksheet.set_column(7, 12, 16)
    worksheet.set_column(13, 13, 48, formats["text"])


def _format_raw_recommendations_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 2, 18)
    worksheet.set_column(3, 20, 16)
    worksheet.set_column(21, 24, 18)
    worksheet.set_column(25, 31, 42, formats["text"])


def _format_standard_sheet(worksheet, formats: dict[str, Any]) -> None:
    worksheet.set_column(0, 0, 18)
    worksheet.set_column(1, 1, 28, formats["text"])
    worksheet.set_column(2, 12, 18)


def _build_executive_conclusion(
    summary_metrics: dict[str, Any],
    product_sales: pd.DataFrame,
    purchase_plan: pd.DataFrame,
    analysis_reliability: dict[str, Any],
) -> str:
    low_reliability = (analysis_reliability.get("sku_reliability", []) or [])
    low_count = sum(1 for item in low_reliability if item.get("confidence") == "low")
    to_buy = int(purchase_plan["Итоговое количество"].sum()) if not purchase_plan.empty else 0
    confidence = localize_forecast_confidence(
        (analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence")
    )
    if not product_sales.empty and "total_revenue" in product_sales.columns:
        top_product = product_sales.sort_values("total_revenue", ascending=False).iloc[0]
        first = (
            f"Главный драйвер выручки сейчас — {top_product.get('product_name', 'ключевой SKU')}: "
            f"{format_money_text(top_product.get('total_revenue'))} выручки."
        )
    else:
        first = f"За период анализа сформирована выручка {format_money_text(summary_metrics.get('total_revenue'))}."
    parts = [first]
    if to_buy > 0:
        parts.append(f"К заказу рекомендуется {format_integer_text(to_buy)} ед. по приоритетным позициям.")
    if confidence:
        parts.append(f"Надёжность прогноза — {confidence}.")
    if low_count > 0:
        parts.append(f"SKU с низкой надёжностью: {low_count}.")
    return " ".join(parts)


def _build_next_actions(purchase_plan: pd.DataFrame, analysis_reliability: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not purchase_plan.empty:
        for _, row in purchase_plan[purchase_plan["Итоговое количество"] > 0].head(4).iterrows():
            actions.append(_build_compact_purchase_action(row))
    if not actions:
        actions.append("Критичных закупок не найдено: проверьте риски и ограничения по данным перед подтверждением плана.")
    if (analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence") == "low":
        actions.append("Надёжность прогноза низкая: вручную проверьте ключевые SKU перед закупкой.")
    return actions[:4]


def _build_manual_checks(analysis_reliability: dict[str, Any], data_quality: dict[str, Any]) -> list[str]:
    checks = []
    if data_quality.get("warnings_count", 0):
        checks.append(f"Во входном файле есть предупреждения по качеству данных: {data_quality.get('warnings_count', 0)}.")
    for warning in (analysis_reliability.get("warnings", []) or [])[:3]:
        if isinstance(warning, dict):
            checks.append(str(warning.get("title") or warning.get("message") or "Проверьте ограничения анализа."))
    return checks or ["Критичных ограничений не найдено, но ключевые SKU всё равно стоит проверить вручную."]


def _count_priority(purchase_plan: pd.DataFrame) -> int:
    if purchase_plan.empty or "Приоритет" not in purchase_plan:
        return 0
    labels = purchase_plan["Приоритет"].astype(str)
    return int(labels.str.contains("Высок", case=False, na=False).sum() + labels.str.contains("Крит", case=False, na=False).sum())


def _count_overstock(purchase_plan: pd.DataFrame) -> int:
    if purchase_plan.empty or "Причина" not in purchase_plan.columns:
        return 0
    return int(purchase_plan["Причина"].astype(str).str.contains("излиш", case=False, na=False).sum())


def _normalize_percent_for_excel(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if abs(number) > 1:
        return number / 100
    return number


def _build_compact_purchase_action(row: pd.Series) -> str:
    sku = str(row.get("SKU", "SKU"))
    qty = format_quantity_text(row.get("Итоговое количество"))
    coverage = row.get("Дней покрытия")
    reason = str(row.get("Причина", ""))
    coverage_text = _format_days_from_value_or_reason(coverage, reason)
    risk_text = _format_risk_from_value_or_reason(row.get("Риск дефицита"), reason)
    return f"{sku} · заказать {qty} · риск {risk_text} · запас {coverage_text}"


def _format_days_from_value_or_reason(value: Any, reason: str) -> str:
    try:
        if value not in (None, ""):
            return f"{float(value):.1f}".replace(".", ",") + " дн."
    except (TypeError, ValueError):
        pass
    match = re.search(r"примерно на ([0-9]+(?:[,.][0-9]+)?) дня", reason)
    if match:
        return f"{match.group(1).replace('.', ',')} дн."
    return "нет данных"


def _format_risk_from_value_or_reason(value: Any, reason: str) -> str:
    try:
        if value not in (None, ""):
            number = float(value)
            return format_percent_text(number)
    except (TypeError, ValueError):
        pass
    match = re.search(r"риск дефицита ([0-9]+(?:[,.][0-9]+)?)%", reason)
    if match:
        return f"{match.group(1).replace('.', ',')}%"
    label = str(value or "").strip().lower()
    if label in {"низкий", "низкая"}:
        return "низкий"
    if label in {"средний", "средняя"}:
        return "средний"
    if label in {"высокий", "высокая"}:
        return "высокий"
    return "нет данных"


def _build_revenue_insight(category_chart_df: pd.DataFrame) -> str:
    if category_chart_df.empty:
        return "После анализа здесь появится категория, которая сильнее всего влияет на выручку."
    top = category_chart_df.sort_values("Выручка", ascending=False).iloc[0]
    return f"{top.get('Категория', 'Категория')} — главный драйвер выручки: {format_money_text(top.get('Выручка'))}."


def _build_reliability_insight(analysis_reliability: dict[str, Any]) -> str:
    confidence = localize_forecast_confidence((analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence"))
    low_count = sum(1 for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low")
    if low_count:
        return f"Надёжность прогноза — {confidence.lower()}. {low_count} SKU требуют ручной проверки."
    return f"Надёжность прогноза — {confidence.lower()}. Проверьте ключевые SKU перед подтверждением закупок."


def _format_ratio_text(value: Any) -> str:
    if value is None or value == "":
        return "Нет данных"
    number = float(value)
    if abs(number) <= 1:
        number *= 100
    return f"{number:,.1f}%".replace(",", " ").replace(".", ",")


def _format_decimal_text(value: Any) -> str:
    if value is None or value == "":
        return "Нет данных"
    return f"{float(value):,.1f}".replace(",", " ").replace(".", ",")


def _format_reliability_label(analysis_reliability: dict[str, Any]) -> str:
    forecast_quality = analysis_reliability.get("forecast_quality", {}) or {}
    confidence = localize_forecast_confidence(forecast_quality.get("overall_confidence"))
    score = forecast_quality.get("reliability_score")
    try:
        score_value = int(round(float(score)))
    except (TypeError, ValueError):
        return confidence.capitalize() if confidence else "Нет данных"
    return f"{score_value}/100 · {confidence.lower()}"


def _build_priority_distribution_df(purchase_plan: pd.DataFrame) -> pd.DataFrame:
    if purchase_plan.empty or "Приоритет" not in purchase_plan.columns:
        return pd.DataFrame(columns=["Приоритет", "SKU"])
    return (
        purchase_plan["Приоритет"]
        .fillna("Нет данных")
        .astype(str)
        .value_counts()
        .rename_axis("Приоритет")
        .reset_index(name="SKU")
    )


def _build_label_value_rows(df: pd.DataFrame, label_col: str, value_col: str, formatter, limit: int) -> list[tuple[str, str]]:
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        return [("Нет данных", "—")]
    rows: list[tuple[str, str]] = []
    for _, record in df.head(limit).iterrows():
        rows.append((str(record.get(label_col, "")), formatter(record.get(value_col))))
    return rows


def _build_date_value_rows(df: pd.DataFrame, date_col: str, value_col: str, formatter, limit: int) -> list[tuple[str, str]]:
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return [("Нет данных", "—")]
    rows: list[tuple[str, str]] = []
    prepared = df.copy()
    prepared[date_col] = pd.to_datetime(prepared[date_col], errors="coerce")
    prepared = prepared.dropna(subset=[date_col]).head(limit)
    for _, record in prepared.iterrows():
        rows.append((record[date_col].strftime("%d.%m"), formatter(record.get(value_col))))
    return rows


def _format_money_text_cell(value: Any) -> str:
    return format_money_text(value)


def _build_dashboard_rows(df: pd.DataFrame, columns: list[tuple[str, str]], limit: int) -> list[list[Any]]:
    if df.empty:
        return [["Нет данных", "—"]]
    rows: list[list[Any]] = []
    for _, record in df.head(limit).iterrows():
        row: list[Any] = []
        for column, kind in columns:
            value = record.get(column)
            if kind == "money":
                row.append(format_money_text(value))
            elif kind == "integer":
                row.append(format_integer_text(value))
            else:
                row.append(str(value))
        rows.append(row)
    return rows


def _build_dashboard_date_rows(df: pd.DataFrame, date_col: str, value_col: str, value_header: str, limit: int) -> list[list[Any]]:
    if df.empty:
        return [["Нет данных", "—"]]
    prepared = df.copy()
    prepared[date_col] = pd.to_datetime(prepared[date_col], errors="coerce")
    prepared = prepared.dropna(subset=[date_col]).head(limit)
    rows: list[list[Any]] = []
    for _, record in prepared.iterrows():
        raw_value = record.get(value_col)
        if value_header == "Выручка":
            value = format_money_text(raw_value)
        else:
            value = f"{format_integer_text(raw_value)} ед."
        rows.append([record[date_col].strftime("%d.%m"), value])
    return rows


def _write_dashboard_table_block(
    *,
    worksheet,
    cell: str,
    title: str,
    subtitle: str,
    rows: list[list[Any]],
    formats: dict[str, Any],
    data_bar_col: int,
    color: str,
) -> None:
    start_row = int(cell[1:]) - 1
    start_col = ord(cell[0]) - ord("A")
    end_col = start_col + 4
    worksheet.merge_range(start_row, start_col, start_row, end_col, title, formats["section_title"])
    worksheet.merge_range(start_row + 1, start_col, start_row + 1, end_col, subtitle, formats["dashboard_subnote"])
    body_start = start_row + 2
    body_end = start_row + 12
    for row_index in range(body_start, body_end + 1):
        for col_index in range(start_col, end_col + 1):
            worksheet.write_blank(row_index, col_index, None, formats["soft_box"])
    if not rows:
        return
    column_count = min(len(rows[0]), end_col - start_col + 1)
    headers = ["Показатель", "Значение"] if column_count == 2 else [f"Колонка {index + 1}" for index in range(column_count)]
    for col_offset, header in enumerate(headers[:column_count]):
        worksheet.write(body_start, start_col + col_offset, header, formats["table_header"])
    numeric_values: list[float] = []
    for row_offset, row_values in enumerate(rows[:8], start=1):
        for col_offset, value in enumerate(row_values[:column_count]):
            worksheet.write(body_start + row_offset, start_col + col_offset, value, formats["text"])
        if data_bar_col < len(row_values):
            numeric_values.append(_extract_numeric(row_values[data_bar_col]))
    if numeric_values:
        data_col = start_col + data_bar_col
        first_data_row = body_start + 1
        last_data_row = body_start + min(len(rows), 8)
        worksheet.conditional_format(
            first_data_row,
            data_col,
            last_data_row,
            data_col,
            {"type": "data_bar", "bar_color": color},
        )


def _write_dashboard_heatmap_block(
    *,
    worksheet,
    cell: str,
    title: str,
    subtitle: str,
    matrix: list[list[float]],
    summary_rows: list[list[Any]],
    formats: dict[str, Any],
) -> None:
    start_row = int(cell[1:]) - 1
    start_col = ord(cell[0]) - ord("A")
    end_col = start_col + 3
    worksheet.merge_range(start_row, start_col, start_row, end_col, title, formats["section_title"])
    worksheet.merge_range(start_row + 1, start_col, start_row + 1, end_col, subtitle, formats["dashboard_subnote"])
    labels_rows = ["A", "B", "C"]
    labels_cols = ["X", "Y", "Z"]
    worksheet.write(start_row + 3, start_col + 1, "X", formats["table_header"])
    worksheet.write(start_row + 3, start_col + 2, "Y", formats["table_header"])
    worksheet.write(start_row + 3, start_col + 3, "Z", formats["table_header"])
    for row_offset, label in enumerate(labels_rows, start=4):
        worksheet.write(start_row + row_offset, start_col, label, formats["table_header"])
        for col_offset, value in enumerate(matrix[row_offset - 4], start=1):
            fmt = _heatmap_format(formats, value)
            worksheet.write_number(start_row + row_offset, start_col + col_offset, value, fmt)


def _build_abc_xyz_heatmap(matrix: list[dict[str, Any]]) -> list[list[float]]:
    grid = {"A": {"X": 0.0, "Y": 0.0, "Z": 0.0}, "B": {"X": 0.0, "Y": 0.0, "Z": 0.0}, "C": {"X": 0.0, "Y": 0.0, "Z": 0.0}}
    for item in matrix:
        abc = str(item.get("abc_class", "")).upper()
        xyz = str(item.get("xyz_class", "")).upper()
        if abc in grid and xyz in grid[abc]:
            grid[abc][xyz] += 1
    return [[grid["A"]["X"], grid["A"]["Y"], grid["A"]["Z"]], [grid["B"]["X"], grid["B"]["Y"], grid["B"]["Z"]], [grid["C"]["X"], grid["C"]["Y"], grid["C"]["Z"]]]


def _extract_numeric(value: Any) -> float:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit() or ch in ",.-")
    if not digits:
        return 0.0
    try:
        return float(digits.replace(" ", "").replace(",", "."))
    except ValueError:
        return 0.0


def _heatmap_format(formats: dict[str, Any], value: float):
    if value >= 3:
        return formats["heat_high"]
    if value >= 1:
        return formats["heat_medium"]
    return formats["heat_low"]
