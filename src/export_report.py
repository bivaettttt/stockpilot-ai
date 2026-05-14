from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.report_presenter import (
    build_abc_xyz_export_df,
    build_abc_xyz_summary_df,
    build_business_purchase_plan_df,
    build_reliability_distribution_df,
    build_technical_recommendations_df,
    build_top_risks_df,
    localize_value,
    shorten_text,
)

DEFAULT_OUTPUT_FILE = Path("data/output/stockpilot_report.xlsx")

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
            insights=insights,
            purchase_plan=prepared_purchase_plan,
            recommendations=recommendations,
            top_risks=prepared_risks.head(5),
            analysis_reliability=analysis_reliability,
            data_quality=data_quality,
        )
        _write_chart_sources(
            worksheet=summary_sheet,
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
            source_sheet_name=SHEET_NAMES["summary"],
        )

        for sheet_name, worksheet in writer.sheets.items():
            if sheet_name == SHEET_NAMES["summary"]:
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
    prepared["date"] = prepared["date"].dt.strftime("%d.%m")
    return prepared.rename(columns={"date": "Дата", "predicted_quantity": "Прогноз спроса"})


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
        "source_filename": source_filename or "Локальный файл",
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


def _write_summary_sheet(
    *,
    worksheet,
    formats: dict[str, Any],
    meta: dict[str, Any],
    summary_metrics: dict[str, Any],
    insights: list[str],
    purchase_plan: pd.DataFrame,
    recommendations: pd.DataFrame | None,
    top_risks: pd.DataFrame,
    analysis_reliability: dict[str, Any],
    data_quality: dict[str, Any],
) -> None:
    worksheet.hide_gridlines(2)
    worksheet.freeze_panes(0, 0)
    worksheet.set_zoom(95)
    worksheet.set_column("A:A", 2)
    worksheet.set_column("B:B", 20)
    worksheet.set_column("C:H", 16)
    worksheet.set_column("I:I", 18)
    worksheet.set_column("J:N", 20)
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
    worksheet.write("J6", "Горизонт прогноза", formats["meta_label"])
    worksheet.write("K6", f"{meta['horizon']} дн.", formats["meta_value"])

    worksheet.merge_range("B6:N7", _build_executive_conclusion(insights, purchase_plan, analysis_reliability), formats["executive_box"])

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
        ("Качество данных", data_quality.get("completeness_score", 0) / 100 if data_quality else None, "ratio"),
        ("Надёжность", (analysis_reliability.get("forecast_quality", {}) or {}).get("reliability_score"), "integer"),
    ]
    positions = ["B9", "D9", "F9", "H9", "J9", "L9", "B13", "D13"]
    for (label, value, style), cell in zip(kpis, positions):
        _write_kpi_card(worksheet, cell, label, value, style, formats)

    worksheet.write("B17", "Что сделать в первую очередь", formats["section_title"])
    next_actions = _build_next_actions(purchase_plan, analysis_reliability)
    for index, action in enumerate(next_actions, start=18):
        worksheet.write(f"B{index}", f"{index - 17}.", formats["list_index"])
        worksheet.merge_range(f"C{index}:H{index}", action, formats["list_text"])

    worksheet.write("J17", "Что проверить вручную", formats["section_title"])
    for index, action in enumerate(_build_manual_checks(analysis_reliability, data_quality), start=18):
        worksheet.write(f"J{index}", f"{index - 17}.", formats["list_index"])
        worksheet.merge_range(f"K{index}:N{index}", action, formats["list_text"])

    worksheet.write("B23", "Топ-5 закупочных рекомендаций", formats["section_title"])
    _write_small_table(
        worksheet,
        start_row=23,
        start_col=1,
        df=(purchase_plan[purchase_plan["Итоговое количество"] > 0].head(5) if not purchase_plan.empty else purchase_plan),
        formats=formats,
    )

    worksheet.write("J23", "Топ-5 рисков", formats["section_title"])
    _write_small_table(
        worksheet,
        start_row=23,
        start_col=9,
        df=top_risks.head(5),
        formats=formats,
    )

    worksheet.write("B31", "Надёжность прогноза", formats["section_title"])
    reliability = analysis_reliability.get("forecast_quality", {}) or {}
    reliability_rows = [
        ("Уровень", localize_value(reliability.get("overall_confidence")) or "Нет данных"),
        ("WAPE", _format_ratio_text(reliability.get("wape"))),
        ("MAE", _format_decimal_text(reliability.get("mae"))),
        ("Bias", _format_ratio_text(reliability.get("bias"))),
    ]
    row = 32
    for label, value in reliability_rows:
        worksheet.write(f"B{row}", label, formats["meta_label"])
        worksheet.write(f"C{row}", value, formats["meta_value"])
        row += 1


def _write_chart_sources(
    *,
    worksheet,
    category_chart_data: pd.DataFrame,
    top_products_chart_data: pd.DataFrame,
    forecast_chart_data: pd.DataFrame,
    reliability_distribution: pd.DataFrame,
    abc_distribution: pd.DataFrame,
) -> None:
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
        worksheet.insert_chart("F13", chart, {"x_scale": 1.1, "y_scale": 1.1})

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
        worksheet.insert_chart("J13", chart, {"x_scale": 1.1, "y_scale": 1.1})

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
        worksheet.insert_chart("F31", chart, {"x_scale": 1.1, "y_scale": 1.05})

    if not chart_sources["reliability"].empty:
        chart = workbook.add_chart({"type": "doughnut"})
        start_row, length = source_map["reliability"]
        chart.add_series(
            {
                "name": "Распределение надёжности",
                "categories": [source, start_row + 1, col, start_row + length, col],
                "values": [source, start_row + 1, col + 1, start_row + length, col + 1],
            }
        )
        chart.set_title({"name": "Надёжность SKU"})
        chart.set_hole_size(60)
        worksheet.insert_chart("J31", chart, {"x_scale": 0.95, "y_scale": 0.95})

    if not chart_sources["abc"].empty:
        chart = workbook.add_chart({"type": "column"})
        start_row, length = source_map["abc"]
        chart.add_series(
            {
                "name": "SKU по классам",
                "categories": [source, start_row + 1, col, start_row + length, col],
                "values": [source, start_row + 1, col + 1, start_row + length, col + 1],
                "fill": {"color": "#F59E0B"},
                "border": {"none": True},
            }
        )
        chart.set_title({"name": "ABC/XYZ распределение"})
        chart.set_legend({"none": True})
        worksheet.insert_chart("F40", chart, {"x_scale": 1.1, "y_scale": 1.0})


def _create_formats(workbook) -> dict[str, Any]:
    return {
        "hero_title": workbook.add_format({"bold": True, "font_size": 22, "font_color": "#0F172A"}),
        "hero_subtitle": workbook.add_format({"font_size": 11, "font_color": "#475569"}),
        "meta_label": workbook.add_format({"font_size": 10, "font_color": "#64748B", "bold": True}),
        "meta_value": workbook.add_format({"font_size": 10, "font_color": "#0F172A"}),
        "executive_box": workbook.add_format(
            {"text_wrap": True, "valign": "vcenter", "fg_color": "#EFF6FF", "border": 1, "border_color": "#BFDBFE"}
        ),
        "card_label": workbook.add_format({"font_size": 9, "font_color": "#64748B", "align": "center"}),
        "card_value_money": workbook.add_format({"font_size": 16, "bold": True, "num_format": '#,##0 "₽"', "align": "center"}),
        "card_value_integer": workbook.add_format({"font_size": 16, "bold": True, "num_format": "#,##0", "align": "center"}),
        "card_value_ratio": workbook.add_format({"font_size": 16, "bold": True, "num_format": '0.0"%"', "align": "center"}),
        "card_note": workbook.add_format({"font_size": 9, "font_color": "#475569", "align": "center"}),
        "card_box": workbook.add_format({"border": 1, "border_color": "#E2E8F0", "fg_color": "#FFFFFF"}),
        "section_title": workbook.add_format({"bold": True, "font_size": 13, "font_color": "#0F172A"}),
        "list_index": workbook.add_format({"bold": True, "font_color": "#2563EB"}),
        "list_text": workbook.add_format({"text_wrap": True, "font_color": "#0F172A"}),
        "table_header": workbook.add_format(
            {"bold": True, "font_color": "#FFFFFF", "fg_color": "#0F172A", "border": 1, "border_color": "#0F172A", "align": "center", "valign": "vcenter"}
        ),
        "text": workbook.add_format({"text_wrap": True, "valign": "top"}),
        "money": workbook.add_format({"num_format": '#,##0 "₽"'}),
        "integer": workbook.add_format({"num_format": "#,##0"}),
        "decimal": workbook.add_format({"num_format": "#,##0.0"}),
        "ratio": workbook.add_format({"num_format": '0.0"%"'}),
        "date": workbook.add_format({"num_format": "dd.mm.yyyy"}),
        "priority_high": workbook.add_format({"fg_color": "#FEF3C7", "font_color": "#92400E"}),
        "priority_critical": workbook.add_format({"fg_color": "#FEE2E2", "font_color": "#991B1B"}),
        "priority_medium": workbook.add_format({"fg_color": "#DBEAFE", "font_color": "#1D4ED8"}),
        "priority_low": workbook.add_format({"fg_color": "#E2E8F0", "font_color": "#334155"}),
        "status_done": workbook.add_format({"fg_color": "#DCFCE7", "font_color": "#166534"}),
        "status_in_purchase": workbook.add_format({"fg_color": "#E0F2FE", "font_color": "#075985"}),
        "status_new": workbook.add_format({"fg_color": "#F8FAFC", "font_color": "#334155"}),
    }


def _write_kpi_card(worksheet, cell: str, label: str, value: Any, style: str, formats: dict[str, Any]) -> None:
    row = int(cell[1:])
    col = ord(cell[0]) - ord("A")
    worksheet.merge_range(row - 1, col, row, col + 1, "", formats["card_box"])
    worksheet.write(row - 1, col, label, formats["card_label"])
    fmt = formats["card_value_integer"]
    if style == "money":
        fmt = formats["card_value_money"]
    elif style == "ratio":
        fmt = formats["card_value_ratio"]
        if value is not None:
            value = float(value) if float(value) <= 1 else float(value) / 100
    worksheet.write(row, col, 0 if value is None else value, fmt)


def _write_small_table(worksheet, *, start_row: int, start_col: int, df: pd.DataFrame, formats: dict[str, Any]) -> None:
    if df is None or df.empty:
        worksheet.write(start_row + 1, start_col, "Нет данных", formats["meta_value"])
        return
    for col_offset, column in enumerate(df.columns[:5]):
        worksheet.write(start_row + 1, start_col + col_offset, column, formats["table_header"])
    for row_offset, (_, values) in enumerate(df.iloc[:, :5].iterrows(), start=2):
        for col_offset, value in enumerate(values):
            worksheet.write(start_row + row_offset, start_col + col_offset, value, formats["text"])


def _format_sheet_base(worksheet, formats: dict[str, Any]) -> None:
    worksheet.freeze_panes(1, 0)
    worksheet.set_row(0, 24, formats["table_header"])
    worksheet.autofilter(0, 0, max(1, worksheet.dim_rowmax), max(1, worksheet.dim_colmax))


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
    insights: list[str],
    purchase_plan: pd.DataFrame,
    analysis_reliability: dict[str, Any],
) -> str:
    if insights:
        return insights[0]
    low_reliability = (analysis_reliability.get("sku_reliability", []) or [])
    low_count = sum(1 for item in low_reliability if item.get("confidence") == "low")
    order_count = int((purchase_plan["Итоговое количество"] > 0).sum()) if not purchase_plan.empty else 0
    return (
        f"В фокусе {order_count} позиций к закупке. "
        f"SKU с низкой надёжностью прогноза: {low_count}. "
        "Начните с высокоприоритетных товаров и проверьте ограничения по качеству данных."
    )


def _build_next_actions(purchase_plan: pd.DataFrame, analysis_reliability: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not purchase_plan.empty:
        for _, row in purchase_plan[purchase_plan["Итоговое количество"] > 0].head(3).iterrows():
            actions.append(
                f"{row['SKU']} — {row['Товар']}: {row['Причина'] or 'Проверьте покрытие и спрос вручную.'}"
            )
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
