from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Any

import pandas as pd

from src.report_presenter import (
    build_abc_xyz_export_df,
    build_abc_xyz_summary_df,
    build_business_purchase_plan_df,
    build_reliability_distribution_df,
    build_top_risks_df,
    format_days_text,
    format_integer_text,
    format_money_text,
    format_percent_text,
    format_quantity_text,
    localize_forecast_confidence,
    localize_value,
    shorten_text,
)

DEFAULT_DASHBOARD_FILE = Path("data/output/dashboard.html")

PRIORITY_STYLES = {
    "Критический": "critical",
    "Высокий": "high",
    "Средний": "medium",
    "Низкий": "low",
    "Информация": "info",
}


def export_dashboard_html(
    output_file: str | Path = DEFAULT_DASHBOARD_FILE,
    *,
    source_filename: str | None = None,
    generated_at: Any | None = None,
    parameters: dict[str, Any] | None = None,
    summary_metrics: dict[str, Any] | None = None,
    insights: list[str] | None = None,
    product_sales: pd.DataFrame | None = None,
    product_forecast: pd.DataFrame | None = None,
    category_sales: pd.DataFrame | None = None,
    daily_sales: pd.DataFrame | None = None,
    daily_forecast_chart_data: pd.DataFrame | None = None,
    recommendations: pd.DataFrame | None = None,
    abc_xyz_matrix: list[dict[str, Any]] | None = None,
    abc_xyz_summary: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    analysis_reliability: dict[str, Any] | None = None,
) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = _build_html(
        source_filename=source_filename,
        generated_at=generated_at,
        parameters=parameters or {},
        summary_metrics=summary_metrics or {},
        insights=insights or [],
        product_sales=product_sales,
        product_forecast=product_forecast,
        category_sales=category_sales,
        daily_sales=daily_sales,
        daily_forecast_chart_data=daily_forecast_chart_data,
        recommendations=recommendations,
        abc_xyz_matrix=abc_xyz_matrix or [],
        abc_xyz_summary=abc_xyz_summary or {},
        data_quality=data_quality or {},
        analysis_reliability=analysis_reliability or {},
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path


def _build_html(
    *,
    source_filename: str | None,
    generated_at: Any,
    parameters: dict[str, Any],
    summary_metrics: dict[str, Any],
    insights: list[str],
    product_sales: pd.DataFrame | None,
    product_forecast: pd.DataFrame | None,
    category_sales: pd.DataFrame | None,
    daily_sales: pd.DataFrame | None,
    daily_forecast_chart_data: pd.DataFrame | None,
    recommendations: pd.DataFrame | None,
    abc_xyz_matrix: list[dict[str, Any]],
    abc_xyz_summary: dict[str, Any],
    data_quality: dict[str, Any],
    analysis_reliability: dict[str, Any],
) -> str:
    purchase_plan = build_business_purchase_plan_df(recommendations)
    top_risks = build_top_risks_df(recommendations, limit=6)
    reliability_distribution = build_reliability_distribution_df(analysis_reliability)
    abc_df = build_abc_xyz_export_df(abc_xyz_matrix, localized=True)
    abc_summary_df = build_abc_xyz_summary_df(abc_xyz_summary)
    risk_distribution = _build_priority_distribution_df(purchase_plan)

    period = _build_period_text(daily_sales)
    generated_text = pd.to_datetime(generated_at or pd.Timestamp.now()).strftime("%d.%m.%Y %H:%M")
    filename_display = _truncate_middle(source_filename or "Файл анализа", 34)
    executive = _build_executive_text(
        summary_metrics=summary_metrics,
        product_sales=product_sales,
        purchase_plan=purchase_plan,
        analysis_reliability=analysis_reliability,
    )

    total_revenue = summary_metrics.get("total_revenue", 0)
    total_units = summary_metrics.get("total_units_sold", 0)
    sku_count = summary_metrics.get("unique_products", 0)
    procurement_units = int(purchase_plan["Итоговое количество"].sum()) if not purchase_plan.empty else 0
    reliability = analysis_reliability.get("forecast_quality", {}) or {}
    forecast_confidence = localize_forecast_confidence(reliability.get("overall_confidence"))
    data_quality_score = data_quality.get("completeness_score")

    category_source = category_sales if category_sales is not None else pd.DataFrame()
    product_source = product_sales if product_sales is not None else pd.DataFrame()
    category_chart = _build_svg_bar_chart(
        title="Выручка по категориям",
        labels=list(category_source.get("category", pd.Series(dtype=str)).head(6)),
        values=list(category_source.get("total_revenue", pd.Series(dtype=float)).head(6)),
        formatter=_format_money,
        color="#2563eb",
    )
    top_products_chart = _build_svg_bar_chart(
        title="Топ товаров по выручке",
        labels=list(product_source.get("product_name", pd.Series(dtype=str)).head(6)),
        values=list(product_source.get("total_revenue", pd.Series(dtype=float)).head(6)),
        formatter=_format_money,
        color="#0f766e",
    )
    sales_trend_chart = _build_svg_line_chart(
        _prepare_daily_sales_points(daily_sales),
        title="Продажи по дням",
        color="#2563eb",
    )
    forecast_chart = _build_svg_line_chart(
        _prepare_forecast_points(daily_forecast_chart_data),
        title="Прогноз спроса по дням",
        color="#7c3aed",
    )
    reliability_chart = _build_svg_bar_chart(
        title="Распределение надёжности SKU",
        labels=list(reliability_distribution.get("Надёжность", pd.Series(dtype=str))),
        values=list(reliability_distribution.get("SKU", pd.Series(dtype=float))),
        formatter=lambda value: f"{int(value)} SKU",
        color="#7c3aed",
    )
    risk_chart = _build_svg_priority_chart(
        title="Распределение приоритетов",
        labels=list(risk_distribution.get("Приоритет", pd.Series(dtype=str))),
        values=list(risk_distribution.get("SKU", pd.Series(dtype=float))),
    )
    abc_chart = _build_svg_bar_chart(
        title="Распределение ABC/XYZ",
        labels=list(abc_summary_df.get("Класс", pd.Series(dtype=str))),
        values=list(abc_summary_df.get("SKU", pd.Series(dtype=float))),
        formatter=lambda value: f"{int(value)} SKU",
        color="#f59e0b",
    )
    abc_heatmap = _build_abc_heatmap_svg(abc_xyz_matrix)

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StockPilot AI — управленческий отчёт</title>
  <style>
    :root {{
      --bg: #f4f7fb;
      --surface: rgba(255,255,255,0.92);
      --surface-2: #f8fafc;
      --text: #0f172a;
      --muted: #64748b;
      --line: #dbe3ef;
      --blue: #2563eb;
      --teal: #0f766e;
      --amber: #f59e0b;
      --violet: #7c3aed;
      --red: #dc2626;
      --radius: 26px;
      --shadow: 0 24px 56px rgba(15, 23, 42, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(37,99,235,0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(15,118,110,0.12), transparent 30%),
        var(--bg);
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 28px 36px 36px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 22px;
      padding: 24px;
      border-radius: 34px;
      background: linear-gradient(160deg, rgba(255,255,255,0.94), rgba(248,250,252,0.9));
      border: 1px solid rgba(219,227,239,0.88);
      box-shadow: var(--shadow);
      min-height: 260px;
    }}
    .hero h1 {{ margin: 0; font-size: 36px; line-height: 1.02; }}
    .hero p {{ margin: 10px 0 0; color: var(--muted); line-height: 1.5; max-width: 760px; }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      align-content: start;
    }}
    .meta-card, .card {{
      border-radius: var(--radius);
      background: var(--surface);
      border: 1px solid rgba(219,227,239,0.9);
      box-shadow: var(--shadow);
    }}
    .meta-card {{ padding: 13px 15px; min-width: 0; overflow: hidden; }}
    .meta-label {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
    .meta-value {{ margin-top: 5px; font-size: 15px; font-weight: 750; min-width: 0; max-width: 100%; overflow-wrap: anywhere; word-break: break-word; line-height: 1.2; }}
    .meta-value.file-name {{ overflow-wrap: anywhere; word-break: break-all; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;
      background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;
    }}
    .executive-strip {{
      margin-top: 18px;
      padding: 22px;
      border-radius: 30px;
      background: linear-gradient(135deg, #0f172a, #1e3a8a 56%, #0f766e);
      color: white;
      box-shadow: var(--shadow);
    }}
    .executive-strip h2 {{ margin: 0 0 10px; font-size: 24px; }}
    .executive-strip p {{ margin: 0; max-width: 1080px; font-size: 18px; line-height: 1.65; color: rgba(255,255,255,0.86); }}
    .grid {{ display: grid; gap: 18px; margin-top: 20px; }}
    .kpis {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .two {{ grid-template-columns: 1.08fr 0.92fr; align-items: start; }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .card {{ padding: 22px; }}
    .card h2 {{ margin: 0 0 6px; font-size: 19px; }}
    .report-section {{ margin-top: 26px; }}
    .report-section > h2 {{ margin: 0; font-size: 24px; letter-spacing: -0.01em; }}
    .eyebrow {{ color: var(--muted); font-size: 13px; margin-bottom: 14px; }}
    .kpi-label {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
    .kpi-value {{ font-size: 29px; font-weight: 850; margin-bottom: 6px; letter-spacing: -0.02em; }}
    .kpi-note {{ color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .status-line {{ display: inline-flex; align-items: center; gap: 8px; }}
    .status-dot {{ width: 9px; height: 9px; border-radius: 999px; background: var(--blue); }}
    .status-dot.good {{ background: #0f766e; }}
    .status-dot.warn {{ background: #f59e0b; }}
    .status-dot.bad {{ background: #dc2626; }}
    .decision-summary {{
      margin-top: 18px; padding: 22px; border-radius: 30px;
      background: linear-gradient(135deg, #0f172a, #1e3a8a 52%, #0f766e);
      color: white; box-shadow: var(--shadow);
    }}
    .decision-summary h2 {{ margin: 0 0 8px; font-size: 24px; }}
    .decision-summary .lead {{ margin: 0; max-width: 1120px; font-size: 17px; line-height: 1.45; color: rgba(255,255,255,0.9); }}
    .facts {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }}
    .fact {{ padding: 11px 13px; border-radius: 16px; background: rgba(255,255,255,0.11); border: 1px solid rgba(255,255,255,0.18); }}
    .fact span {{ display: block; color: rgba(255,255,255,0.68); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .fact strong {{ display: block; margin-top: 4px; font-size: 17px; }}
    .decision-board {{ grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: start; }}
    .decision-column {{ padding: 20px; border-radius: 26px; background: var(--surface); border: 1px solid rgba(219,227,239,0.92); box-shadow: var(--shadow); }}
    .decision-column h2 {{ margin: 0 0 4px; font-size: 18px; }}
    .decision-card {{ margin-top: 12px; padding: 13px 14px; border-radius: 18px; background: var(--surface-2); border: 1px solid var(--line); min-height: 82px; }}
    .decision-card strong {{ display: block; font-size: 15px; margin-bottom: 5px; }}
    .decision-card .meta {{ color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .purchase-cards {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .purchase-card, .risk-card {{ padding: 15px; border-radius: 18px; background: var(--surface-2); border: 1px solid var(--line); }}
    .purchase-card strong, .risk-card strong {{ display:block; margin-bottom:5px; }}
    .details-block {{ margin-top: 16px; border: 1px solid var(--line); border-radius: 18px; background: #fff; overflow: hidden; }}
    .details-block summary {{ cursor: pointer; padding: 14px 16px; font-weight: 700; color: var(--text); background: var(--surface-2); }}
    .details-block .details-body {{ padding: 12px 16px 16px; }}
    .stack {{ display: grid; gap: 12px; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }}
    .summary-chip {{ padding: 14px 16px; border-radius: 18px; background: var(--surface-2); border: 1px solid var(--line); }}
    .summary-chip strong {{ display: block; font-size: 22px; margin-top: 6px; }}
    .list-item {{
      display: grid; grid-template-columns: 26px 1fr; gap: 12px;
      padding: 14px; border-radius: 18px; background: var(--surface-2); border: 1px solid var(--line);
    }}
    .list-index {{
      width: 26px; height: 26px; border-radius: 999px; display: grid; place-items: center;
      font-weight: 700; background: #dbeafe; color: #1d4ed8;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }}
    th {{ text-align: left; color: var(--muted); font-weight: 700; padding: 12px 10px; border-bottom: 1px solid var(--line); white-space: nowrap; }}
    td {{ padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: break-word; }}
    .tag {{
      display: inline-flex; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
    }}
    .critical {{ background: #fee2e2; color: #991b1b; }}
    .high {{ background: #fee2e2; color: #991b1b; }}
    .medium {{ background: #fef3c7; color: #92400e; }}
    .low {{ background: #dbeafe; color: #1d4ed8; }}
    .info {{ background: #dcfce7; color: #166534; }}
    .muted {{ color: var(--muted); }}
    .chart-card {{ padding: 18px; border-radius: 24px; background: linear-gradient(180deg, #ffffff, #f8fafc); border: 1px solid var(--line); }}
    .chart-title {{ font-size: 15px; font-weight: 760; margin-bottom: 10px; }}
    .insight {{ margin-top: 12px; color: var(--muted); line-height: 1.55; }}
    .matrix-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; }}
    .matrix-cell {{ min-height: 72px; border-radius: 18px; display: grid; place-items: center; text-align: center; border: 1px solid var(--line); background: #f8fafc; }}
    .matrix-cell strong {{ font-size: 22px; }}
    svg text {{ font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #475569; font-size: 13px; }}
    .footer {{ margin-top: 26px; text-align: center; color: var(--muted); font-size: 13px; }}
    @media print {{
      body {{ background: white; }}
      main {{ padding: 10mm; }}
      .hero, .card, .meta-card {{ box-shadow: none; }}
      .grid, .hero {{ break-inside: avoid; }}
    }}
    @media (max-width: 1080px) {{
      .hero, .kpis, .two, .three, .summary-grid, .decision-board, .facts, .purchase-cards {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 760px) {{
      main {{ padding: 18px; }}
      .hero, .kpis, .two, .three, .meta-grid, .summary-grid, .decision-board, .facts, .purchase-cards {{ grid-template-columns: 1fr; }}
      .hero h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <div class="badge">Управленческий отчёт StockPilot AI</div>
        <h1 style="margin-top:14px;">StockPilot AI</h1>
        <p>От файла к решению: спрос, риск дефицита, закупочный план, надёжность прогноза и ABC/XYZ в одном отчёте.</p>
      </div>
      <div class="meta-grid">
        <div class="meta-card"><div class="meta-label">Файл</div><div class="meta-value file-name" title="{escape(source_filename or 'Файл анализа')}">{escape(filename_display)}</div></div>
        <div class="meta-card"><div class="meta-label">Дата анализа</div><div class="meta-value">{generated_text}</div></div>
        <div class="meta-card"><div class="meta-label">Период</div><div class="meta-value">{escape(period)}</div></div>
        <div class="meta-card"><div class="meta-label">SKU / строк</div><div class="meta-value">{int(sku_count)} / {int((data_quality or {}).get("total_rows", 0) or 0)}</div></div>
        <div class="meta-card"><div class="meta-label">Горизонт прогноза</div><div class="meta-value">{int(parameters.get("horizon", 0) or 0)} дн.</div></div>
        <div class="meta-card"><div class="meta-label">Источник</div><div class="meta-value">StockPilot AI</div></div>
      </div>
    </section>

    {_render_decision_summary(executive, purchase_plan, top_risks, analysis_reliability, data_quality)}

    <section class="report-section">
      <h2>Решения на сегодня</h2>
      <div class="grid decision-board">
        {_render_decision_column("Заказать", "Позиции, которые попадают в закупочный фокус", _build_order_decisions(purchase_plan))}
        {_render_decision_column("Проверить", "Риски, качество данных и слабая надёжность", _build_check_decisions(top_risks, data_quality, analysis_reliability))}
        {_render_decision_column("Наблюдать", "Позиции без срочного действия, но с регулярным контролем", _build_control_decisions(purchase_plan, analysis_reliability))}
      </div>
    </section>

    <section class="grid kpis">
      {_kpi_card("Выручка", _format_money(total_revenue), "Фактическая выручка за анализируемый период")}
      {_kpi_card("Продано единиц", _format_units(total_units), "Суммарный объём продаж")}
      {_kpi_card("SKU в анализе", f"{int(sku_count)}", "Товары, которые вошли в расчёт")}
      {_kpi_card("К закупке", _format_units(procurement_units), "Суммарный объём заказа по текущему плану")}
      {_kpi_card("Качество данных", _format_percent_like(data_quality_score), "Полнота входного файла", _quality_status_class(data_quality_score))}
      {_kpi_card("Надёжность прогноза", forecast_confidence.capitalize(), "Оценка доверия к прогнозу", _confidence_status_class(reliability.get("overall_confidence")))}
      {_kpi_card("WAPE", _format_ratio(reliability.get("wape")), "Ошибка прогноза с учётом объёма продаж", _wape_status_class(reliability.get("wape")))}
      {_kpi_card("Bias", _format_ratio(reliability.get("bias")), "Смещение: завышает или занижает спрос")}
    </section>

    <section class="grid two">
      <article class="card">
        <h2>Деньги</h2>
        <div class="eyebrow">Категории, товары и спрос</div>
        <div class="summary-grid">{_render_revenue_summary(category_source, product_source)}</div>
        <div class="chart-card">{category_chart}</div>
        <div class="insight">{escape(_build_revenue_insight(category_source))}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{top_products_chart}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{sales_trend_chart}</div>
      </article>
      <article class="card">
        <h2>Прогноз</h2>
        <div class="eyebrow">Надёжность прогноза и SKU, которые стоит проверить</div>
        <div class="summary-grid">{_render_reliability_chips(reliability, reliability_distribution)}</div>
        <div class="chart-card">{forecast_chart}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{reliability_chart}</div>
        <div class="insight">{escape(_build_reliability_insight(analysis_reliability))}</div>
        <div style="height:14px;"></div>
        <div class="stack">{_render_reliability_list(analysis_reliability)}</div>
      </article>
    </section>

    <section class="grid two">
      <article class="card">
        <h2>Закупочный план</h2>
        <div class="eyebrow">Приоритеты закупки и ключевые позиции к заказу</div>
        <div class="summary-grid">{_render_purchase_summary(purchase_plan)}</div>
        <div class="chart-card">{risk_chart}</div>
        <div style="height:14px;"></div>
        {_render_purchase_cards(purchase_plan)}
        <details class="details-block">
          <summary>Показать подробную таблицу закупочного плана</summary>
          <div class="details-body table-wrap">{_render_purchase_plan_table(purchase_plan)}</div>
        </details>
      </article>
      <article class="card">
        <h2>Риски</h2>
        <div class="eyebrow">Очередь рисков и конкретные действия</div>
        {_render_risk_cards(top_risks)}
        <details class="details-block">
          <summary>Показать таблицу рисков</summary>
          <div class="details-body table-wrap">{_render_risk_table(top_risks)}</div>
        </details>
      </article>
    </section>

    <section class="grid two">
      <article class="card">
        <h2>ABC/XYZ</h2>
        <div class="eyebrow">Классы вклада в выручку и стабильности спроса</div>
        <div class="chart-card">{abc_chart}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{abc_heatmap}</div>
        <div class="insight">A/B/C показывает вклад товара в выручку, X/Y/Z — стабильность спроса. AX обычно требует самого внимательного планирования запаса.</div>
        <div style="height:14px;"></div>
        {_render_abc_interpretation()}
        <details class="details-block">
          <summary>Показать SKU в ABC/XYZ</summary>
          <div class="details-body table-wrap">{_render_abc_table(abc_df)}</div>
        </details>
      </article>
      <article class="card">
        <h2>Качество данных</h2>
        <div class="eyebrow">Что влияет на интерпретацию отчёта</div>
        {_render_data_quality_bars(data_quality)}
        <p class="insight">100% означает полноту и корректность структуры файла. Предупреждения могут сохраняться из-за особенностей спроса, нулевых остатков или интерпретации прогноза.</p>
        <div style="height:14px;"></div>
        {_render_metric_rows([
          ("Всего строк", str(int((data_quality or {}).get("total_rows", 0) or 0))),
          ("Полнота", _format_percent_like((data_quality or {}).get("completeness_score"))),
          ("Корректность", _format_percent_like((data_quality or {}).get("validity_score"))),
          ("Согласованность", _format_percent_like((data_quality or {}).get("consistency_score"))),
          ("Предупреждения", str(int((data_quality or {}).get("warnings_count", 0) or 0))),
          ("Ошибки", str(int((data_quality or {}).get("errors_count", 0) or 0))),
        ])}
      </article>
    </section>

    <div class="footer">Сформировано StockPilot AI. Пояснения основаны на агрегированном контексте текущего анализа.</div>
  </main>
</body>
</html>"""


def _build_period_text(daily_sales: pd.DataFrame | None) -> str:
    if daily_sales is None or daily_sales.empty or "date" not in daily_sales.columns:
        return "Нет данных"
    dates = pd.to_datetime(daily_sales["date"], errors="coerce").dropna()
    if dates.empty:
        return "Нет данных"
    return f"{dates.min().strftime('%d.%m.%Y')} - {dates.max().strftime('%d.%m.%Y')}"


def _truncate_middle(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    keep = max(6, (limit - 1) // 2)
    tail = max(6, limit - keep - 1)
    return f"{value[:keep]}…{value[-tail:]}"


def _build_executive_text(
    *,
    summary_metrics: dict[str, Any],
    product_sales: pd.DataFrame | None,
    purchase_plan: pd.DataFrame,
    analysis_reliability: dict[str, Any],
) -> str:
    product_source = product_sales if product_sales is not None else pd.DataFrame()
    top_product = (
        product_source.sort_values("total_revenue", ascending=False).head(1).to_dict(orient="records")
        if not product_source.empty and "total_revenue" in product_source.columns
        else []
    )
    to_buy = int(purchase_plan["Итоговое количество"].sum()) if not purchase_plan.empty else 0
    low_confidence = sum(
        1 for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low"
    )
    confidence = localize_forecast_confidence(
        (analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence")
    )
    parts: list[str] = []
    if top_product:
        product = top_product[0]
        parts.append(
            f"Главный драйвер выручки сейчас — {product.get('product_name', 'ключевой SKU')}: "
            f"{format_money_text(product.get('total_revenue'))} выручки."
        )
    else:
        parts.append(f"За период анализа сформирована выручка {format_money_text(summary_metrics.get('total_revenue'))}.")
    if to_buy > 0:
        parts.append(f"По текущему плану к заказу рекомендуется {format_integer_text(to_buy)} ед.")
    if confidence:
        parts.append(f"Надёжность прогноза — {confidence}.")
    if low_confidence > 0:
        parts.append(f"SKU с низкой надёжностью: {low_confidence}. Их стоит проверить вручную.")
    return " ".join(parts)


def _render_decision_summary(
    executive: str,
    purchase_plan: pd.DataFrame,
    top_risks: pd.DataFrame,
    analysis_reliability: dict[str, Any],
    data_quality: dict[str, Any],
) -> str:
    to_buy = format_quantity_text(purchase_plan["Итоговое количество"].sum() if not purchase_plan.empty else 0)
    top_risk = "Критичных рисков не найдено"
    if top_risks is not None and not top_risks.empty:
        first = top_risks.iloc[0]
        top_risk = f"{first.get('SKU', 'SKU')} · риск {format_percent_text(first.get('Риск'))}"
    confidence = localize_forecast_confidence((analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence"))
    checks = int(data_quality.get("warnings_count", 0) or 0)
    return f"""
    <section class="decision-summary">
      <h2>Управленческая сводка</h2>
      <p class="lead">{escape(executive)}</p>
      <div class="facts">
        <div class="fact"><span>К заказу</span><strong>{escape(to_buy)}</strong></div>
        <div class="fact"><span>Ключевой риск</span><strong>{escape(top_risk)}</strong></div>
        <div class="fact"><span>Надёжность прогноза</span><strong>{escape(confidence)}</strong></div>
        <div class="fact"><span>Проверить вручную</span><strong>{checks} предупрежд.</strong></div>
      </div>
    </section>
    """


def _kpi_card(label: str, value: str, note: str, status: str | None = None) -> str:
    status_html = f"<span class='status-dot {status}'></span>" if status else ""
    return f"""
    <div class="card">
      <div class="kpi-label">{escape(label)}</div>
      <div class="kpi-value"><span class="status-line">{status_html}{escape(value)}</span></div>
      <div class="kpi-note">{escape(note)}</div>
    </div>
    """


def _quality_status_class(value: Any) -> str:
    percent = _percent_number(value)
    if percent >= 90:
        return "good"
    if percent >= 70:
        return "warn"
    return "bad"


def _confidence_status_class(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw == "high":
        return "good"
    if raw == "medium":
        return "warn"
    return "bad"


def _wape_status_class(value: Any) -> str:
    try:
        number = abs(float(value))
    except (TypeError, ValueError):
        return "warn"
    if number <= 0.2:
        return "good"
    if number <= 0.35:
        return "warn"
    return "bad"


def _render_action_list(items: list[str]) -> str:
    return "".join(
        f"<div class='list-item'><div class='list-index'>{index}</div><div>{escape(item)}</div></div>"
        for index, item in enumerate(items, start=1)
    )


def _build_actions(purchase_plan: pd.DataFrame, top_risks: pd.DataFrame, analysis_reliability: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not purchase_plan.empty:
        for _, row in purchase_plan[purchase_plan["Итоговое количество"] > 0].head(4).iterrows():
            actions.append(_build_compact_purchase_action(row))
    if not top_risks.empty:
        for _, row in top_risks.head(2).iterrows():
            actions.append(f"Проверьте риск по {row['SKU']}: {_ensure_sentence(row['Действие'])}")
    if not actions:
        actions.append("Критичных закупок не найдено. Сфокусируйтесь на рисках и качестве данных.")
    if (analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence") == "low":
        actions.append("Надёжность прогноза низкая: ключевые SKU стоит проверить вручную перед закупкой.")
    return actions[:5]


def _render_decision_column(title: str, subtitle: str, items: list[dict[str, str]]) -> str:
    if not items:
        items = [{"title": "Нет срочных действий", "body": "Проверьте сводку и рабочие таблицы при необходимости."}]
    cards = "".join(
        f"<div class='decision-card'><strong>{escape(item['title'])}</strong><div class='meta'>{escape(item['body'])}</div></div>"
        for item in items[:4]
    )
    return f"""
    <article class="decision-column">
      <h2>{escape(title)}</h2>
      <div class="eyebrow">{escape(subtitle)}</div>
      {cards}
    </article>
    """


def _build_order_decisions(purchase_plan: pd.DataFrame) -> list[dict[str, str]]:
    if purchase_plan.empty:
        return []
    items = []
    rows = purchase_plan[purchase_plan["Итоговое количество"] > 0].head(4)
    for _, row in rows.iterrows():
        items.append(
            {
                "title": f"{row.get('SKU', 'SKU')} · {row.get('Товар', 'Товар')}",
                "body": _build_compact_purchase_action(row).replace(f"{row.get('SKU', 'SKU')} · ", ""),
            }
        )
    return items


def _build_check_decisions(top_risks: pd.DataFrame, data_quality: dict[str, Any], analysis_reliability: dict[str, Any]) -> list[dict[str, str]]:
    items = []
    if top_risks is not None and not top_risks.empty:
        for _, row in top_risks.head(2).iterrows():
            items.append(
                {
                    "title": f"{row.get('SKU', 'SKU')} · риск {format_percent_text(row.get('Риск'))}",
                    "body": shorten_text(row.get("Действие"), 110) or "Проверьте остаток и спрос вручную.",
                }
            )
    if data_quality.get("warnings_count", 0):
        items.append({"title": "Качество данных", "body": f"Есть предупреждения: {int(data_quality.get('warnings_count', 0))}. Проверьте перед закупкой."})
    low_count = sum(1 for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low")
    if low_count:
        items.append({"title": "Надёжность прогноза", "body": f"{low_count} SKU с низкой надёжностью требуют ручной проверки."})
    return items[:4]


def _build_control_decisions(purchase_plan: pd.DataFrame, analysis_reliability: dict[str, Any]) -> list[dict[str, str]]:
    items = []
    if not purchase_plan.empty:
        rows = purchase_plan[purchase_plan["Итоговое количество"] <= 0].head(3)
        for _, row in rows.iterrows():
            items.append(
                {
                    "title": f"{row.get('SKU', 'SKU')} · {row.get('Товар', 'Товар')}",
                    "body": "Активная закупка не требуется. Контролируйте покрытие и спрос.",
                }
            )
    low_items = [
        item for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low"
    ][:2]
    for item in low_items:
        items.append(
            {
                "title": f"{item.get('sku', 'SKU')} · низкая надёжность",
                "body": "Сверьте прогноз с фактическим остатком перед решением.",
            }
        )
    confidence = localize_forecast_confidence((analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence"))
    items.append({"title": "Прогноз", "body": f"Надёжность — {confidence}. Ключевые SKU стоит сверить с реальным остатком."})
    if len(items) < 2:
        items.append(
            {
                "title": "Позиции без срочного заказа",
                "body": "Держите их в регулярном контроле, но не переносите в срочную закупку без проверки спроса.",
            }
        )
    return items[:4]


def _build_compact_purchase_action(row: pd.Series) -> str:
    sku = str(row.get("SKU", "SKU"))
    qty = format_quantity_text(row.get("Итоговое количество"))
    reason = str(row.get("Причина", ""))
    return (
        f"{sku} · заказать {qty} · риск {_extract_risk_text(row.get('Риск дефицита'), reason)} · "
        f"запас {_extract_days_text(row.get('Дней покрытия'), reason)}"
    )


def _extract_days_text(value: Any, reason: str) -> str:
    try:
        if value not in (None, ""):
            return format_days_text(float(value))
    except (TypeError, ValueError):
        pass
    match = re.search(r"примерно на ([0-9]+(?:[,.][0-9]+)?) дня", reason)
    return f"{match.group(1).replace('.', ',')} дн." if match else "нет данных"


def _extract_risk_text(value: Any, reason: str) -> str:
    match = re.search(r"риск дефицита ([0-9]+(?:[,.][0-9]+)?)%", reason)
    if match:
        return f"{match.group(1).replace('.', ',')}%"
    text = str(value or "").strip()
    return text.lower() if text else "нет данных"


def _ensure_sentence(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "Проверьте остаток и спрос вручную."
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _build_checks(data_quality: dict[str, Any], analysis_reliability: dict[str, Any]) -> list[str]:
    checks = []
    if data_quality.get("warnings_count", 0):
        checks.append(f"Есть предупреждения по качеству данных: {int(data_quality.get('warnings_count', 0))}.")
    if data_quality.get("errors_count", 0):
        checks.append(f"Есть ошибки по качеству данных: {int(data_quality.get('errors_count', 0))}.")
    for warning in (analysis_reliability.get("warnings", []) or [])[:3]:
        if isinstance(warning, dict):
            checks.append(str(warning.get("title") or warning.get("message") or "Проверьте ограничения анализа."))
    return checks or ["Критичных ограничений не найдено, но ключевые SKU всё равно стоит проверить вручную."]


def _render_purchase_plan_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='muted'>По текущему прогнозу закупка не требуется.</p>"
    rows = []
    for _, row in df[df["Итоговое количество"] > 0].head(8).iterrows():
        priority = str(row["Приоритет"])
        rows.append(
            f"""
            <tr>
              <td><strong>{escape(str(row['SKU']))}</strong><div class="muted">{escape(str(row['Категория']))}</div></td>
              <td>{escape(str(row['Товар']))}</td>
              <td><span class="tag {PRIORITY_STYLES.get(priority, 'info')}">{escape(priority)}</span></td>
              <td>{_format_units(row['Остаток'])}</td>
              <td>{_format_days(row['Дней покрытия'])}</td>
              <td>{_format_units(row['Итоговое количество'])}</td>
            </tr>
            """
        )
    return f"""
    <table>
      <thead><tr><th>SKU</th><th>Товар</th><th>Приоритет</th><th>Остаток</th><th>Покрытие</th><th>К заказу</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def _render_purchase_cards(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='muted'>По текущему прогнозу закупка не требуется.</p>"
    cards = []
    rows = df[df["Итоговое количество"] > 0].head(6)
    if rows.empty:
        return "<p class='muted'>Активная закупка не требуется.</p>"
    for _, row in rows.iterrows():
        reason = (
            f"Запас {_extract_days_text(row.get('Дней покрытия'), str(row.get('Причина', '')))} · "
            f"риск {_extract_risk_text(row.get('Риск дефицита'), str(row.get('Причина', '')))} · "
            f"к заказу {format_quantity_text(row.get('Итоговое количество'))}"
        )
        cards.append(
            f"""
            <div class="purchase-card">
              <strong>{escape(str(row.get('SKU', 'SKU')))} · {escape(str(row.get('Товар', 'Товар')))}</strong>
              <div class="muted">{escape(str(row.get('Категория', 'Категория')))}</div>
              <div style="margin-top:10px;">К заказу: <strong>{_format_units(row.get('Итоговое количество'))}</strong> · Остаток: {_format_units(row.get('Остаток'))}</div>
              <div class="muted">{escape(reason)}</div>
            </div>
            """
        )
    return f"<div class='purchase-cards'>{''.join(cards)}</div>"


def _render_risk_cards(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='muted'>Критичных рисков не найдено.</p>"
    cards = []
    for _, row in df.head(6).iterrows():
        priority = str(row.get("Приоритет", "Информация"))
        action = shorten_text(row.get("Действие"), 92) or "Проверьте остаток и спрос вручную."
        stock = _format_units(row.get("Остаток")) if "Остаток" in row.index else "нет данных"
        coverage = _format_days(row.get("Дней покрытия")) if "Дней покрытия" in row.index else "нет данных"
        cards.append(
            f"""
            <div class="risk-card">
              <strong>{escape(str(row.get('SKU', 'SKU')))} · {escape(str(row.get('Товар', 'Товар')))}</strong>
              <span class="tag {PRIORITY_STYLES.get(priority, 'info')}">{escape(priority)}</span>
              <div style="margin-top:10px;">Риск: <strong>{escape(format_percent_text(row.get('Риск')))}</strong> · остаток {stock} · запас {coverage}</div>
              <div class="muted">Почему важно: риск дефицита может сорвать продажи до следующей поставки.</div>
              <div style="margin-top:8px;">Действие: {escape(action)}</div>
            </div>
            """
        )
    return f"<div class='stack'>{''.join(cards)}</div>"


def _render_risk_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='muted'>Критичных рисков не найдено.</p>"
    rows = []
    for _, row in df.head(8).iterrows():
        priority = str(row["Приоритет"])
        rows.append(
            f"""
            <tr>
              <td><strong>{escape(str(row['SKU']))}</strong><div class="muted">{escape(str(row['Товар']))}</div></td>
              <td><span class="tag {PRIORITY_STYLES.get(priority, 'info')}">{escape(priority)}</span></td>
              <td>{escape(format_percent_text(row['Риск']))}</td>
              <td>{escape(shorten_text(row['Действие'], 92))}</td>
            </tr>
            """
        )
    return f"""
    <table>
      <thead><tr><th>SKU</th><th>Приоритет</th><th>Риск</th><th>Действие</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def _render_abc_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='muted'>ABC/XYZ-матрица не рассчитана.</p>"
    rows = []
    for _, row in df.head(10).iterrows():
        rows.append(
            f"""
            <tr>
              <td>{escape(str(row['SKU']))}</td>
              <td>{escape(str(row['Товар']))}</td>
              <td>{escape(str(row['Класс ABC/XYZ']))}</td>
              <td>{escape(str(row['Приоритет']))}</td>
              <td>{escape(shorten_text(row['Действие'], 88))}</td>
            </tr>
            """
        )
    return f"""
    <table>
      <thead><tr><th>SKU</th><th>Товар</th><th>Класс</th><th>Приоритет</th><th>Действие</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def _render_metric_rows(rows: list[tuple[str, str]]) -> str:
    html = []
    for label, value in rows:
        html.append(
            f"<div style='display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px solid var(--line);'><span class='muted'>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        )
    return "".join(html)


def _render_revenue_summary(category_sales: pd.DataFrame | None, product_sales: pd.DataFrame | None) -> str:
    cards: list[tuple[str, str]] = []
    if category_sales is not None and not category_sales.empty and "total_revenue" in category_sales.columns:
        top = category_sales.sort_values("total_revenue", ascending=False).iloc[0]
        cards.append(("Категория-лидер", f"{top.get('category', 'Категория')} · {format_money_text(top.get('total_revenue'))}"))
    if product_sales is not None and not product_sales.empty and "total_revenue" in product_sales.columns:
        top_products = product_sales.sort_values("total_revenue", ascending=False)
        leader = top_products.iloc[0]
        cards.append(("SKU-лидер", f"{leader.get('product_name', 'Товар')} · {format_money_text(leader.get('total_revenue'))}"))
        total = float(pd.to_numeric(top_products["total_revenue"], errors="coerce").fillna(0).sum() or 0)
        top5 = float(pd.to_numeric(top_products.head(5)["total_revenue"], errors="coerce").fillna(0).sum() or 0)
        if total > 0:
            cards.append(("Доля топ-5", format_percent_text(top5 / total)))
    if not cards:
        cards = [("Деньги", "Нет данных")]
    return "".join(
        f"<div class='summary-chip'><span class='muted'>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in cards[:3]
    )


def _render_data_quality_bars(data_quality: dict[str, Any]) -> str:
    rows = [
        ("Полнота", data_quality.get("completeness_score")),
        ("Корректность", data_quality.get("validity_score")),
        ("Согласованность", data_quality.get("consistency_score")),
    ]
    html = []
    for label, value in rows:
        percent = _percent_number(value)
        html.append(
            f"""
            <div style='margin-bottom:12px;'>
              <div style='display:flex;justify-content:space-between;gap:16px;margin-bottom:6px;'>
                <span class='muted'>{escape(label)}</span><strong>{escape(format_percent_text(value))}</strong>
              </div>
              <div style='height:10px;border-radius:999px;background:#e2e8f0;overflow:hidden;'>
                <div style='height:100%;width:{percent:.1f}%;border-radius:999px;background:linear-gradient(90deg,#2563eb,#0f766e);'></div>
              </div>
            </div>
            """
        )
    return "".join(html)


def _percent_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if abs(number) <= 1:
        number *= 100
    return max(0.0, min(100.0, number))


def _render_purchase_summary(purchase_plan: pd.DataFrame) -> str:
    if purchase_plan.empty:
        return ""
    to_buy = purchase_plan[purchase_plan["Итоговое количество"] > 0]
    suppliers = (
        to_buy["Поставщик"].fillna("").astype(str).replace("Поставщик не указан", "").replace("", pd.NA).dropna().nunique()
        if "Поставщик" in to_buy.columns
        else 0
    )
    cards = [
        ("Позиции к заказу", str(int((to_buy["Итоговое количество"] > 0).sum()))),
        ("Суммарно к заказу", format_quantity_text(to_buy["Итоговое количество"].sum() if not to_buy.empty else 0)),
        ("Поставщики", str(int(suppliers))),
    ]
    return "".join(
        f"<div class='summary-chip'><span class='muted'>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in cards
    )


def _render_abc_interpretation() -> str:
    items = [
        ("AX", "держать в наличии всегда"),
        ("AY", "ключевые товары, планировать внимательно"),
        ("CX/CY", "низкий вклад, закупать осторожнее"),
    ]
    cards = "".join(
        f"<div class='summary-chip'><span class='muted'>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in items
    )
    return f"<div class='summary-grid'>{cards}</div>"


def _render_reliability_chips(reliability: dict[str, Any], distribution: pd.DataFrame) -> str:
    low_count = 0
    if not distribution.empty:
        matched = distribution[distribution["Надёжность"].astype(str).str.contains("Низк", case=False, na=False)]
        if not matched.empty:
            low_count = int(matched.iloc[0]["SKU"])
    cards = [
        ("WAPE", _format_ratio(reliability.get("wape"))),
        ("Bias", _format_ratio(reliability.get("bias"))),
        ("Низкая надёжность", f"{low_count} SKU"),
    ]
    return "".join(
        f"<div class='summary-chip'><span class='muted'>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in cards
    )


def _render_reliability_list(analysis_reliability: dict[str, Any]) -> str:
    items = []
    low_items = [
        item for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low"
    ][:3]
    for item in low_items:
        items.append(
            f"<div class='list-item'><div class='list-index'>!</div><div><strong>{escape(str(item.get('sku', 'SKU')))}</strong> — {escape(str(item.get('reason') or item.get('reliability_reason') or 'Проверьте вручную.'))}</div></div>"
        )
    if not items:
        items.append("<div class='list-item'><div class='list-index'>1</div><div>SKU с критично низкой надёжностью не выявлены.</div></div>")
    return "".join(items)


def _build_revenue_insight(category_sales: pd.DataFrame | None) -> str:
    if category_sales is None or category_sales.empty or "total_revenue" not in category_sales.columns:
        return "После анализа здесь будет видно, какая категория сильнее всего влияет на выручку."
    top = category_sales.sort_values("total_revenue", ascending=False).iloc[0]
    return f"{top.get('category', 'Категория')} — главный драйвер выручки: {format_money_text(top.get('total_revenue'))}."


def _build_reliability_insight(analysis_reliability: dict[str, Any]) -> str:
    confidence = localize_forecast_confidence((analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence"))
    low_count = sum(1 for item in (analysis_reliability.get("sku_reliability", []) or []) if item.get("confidence") == "low")
    if low_count:
        return f"Надёжность прогноза — {confidence}. {low_count} SKU стоит проверить вручную перед закупкой."
    return f"Надёжность прогноза — {confidence}. Ключевые SKU всё равно стоит проверить перед закупкой."


def _build_priority_distribution_df(purchase_plan: pd.DataFrame) -> pd.DataFrame:
    if purchase_plan.empty or "Приоритет" not in purchase_plan.columns:
        return pd.DataFrame(columns=["Приоритет", "SKU"])
    counts = (
        purchase_plan["Приоритет"]
        .fillna("Нет данных")
        .astype(str)
        .value_counts()
        .rename_axis("Приоритет")
        .reset_index(name="SKU")
    )
    return counts


def _build_abc_heatmap_svg(matrix: list[dict[str, Any]]) -> str:
    counts = {"A": {"X": 0, "Y": 0, "Z": 0}, "B": {"X": 0, "Y": 0, "Z": 0}, "C": {"X": 0, "Y": 0, "Z": 0}}
    for item in matrix:
        abc = str(item.get("abc_class", "")).upper()
        xyz = str(item.get("xyz_class", "")).upper()
        if abc in counts and xyz in counts[abc]:
            counts[abc][xyz] += 1
    max_count = max((value for row in counts.values() for value in row.values()), default=0) or 1
    cells = []
    for abc in ["A", "B", "C"]:
        for xyz in ["X", "Y", "Z"]:
            value = counts[abc][xyz]
            intensity = value / max_count
            background = "#fff7ed" if intensity >= 0.66 else "#fffbeb" if intensity > 0 else "#f8fafc"
            cells.append(
                f"<div class='matrix-cell' style='background:{background};'><div><span class='muted'>{abc}{xyz}</span><strong>{value}</strong><div class='muted'>SKU</div></div></div>"
            )
    return f"<div class='chart-title'>ABC/XYZ матрица</div><div class='matrix-grid'>{''.join(cells)}</div>"


def _build_svg_bar_chart(title: str, labels: list[Any], values: list[Any], formatter, color: str) -> str:
    pairs = [(str(label), float(value)) for label, value in zip(labels, values) if label not in (None, "") and pd.notna(value)]
    if not pairs:
        return f"<div class='chart-title'>{escape(title)}</div><p class='muted'>Нет данных для визуализации.</p>"
    max_value = max(value for _, value in pairs) or 1
    rows = []
    for index, (label, value) in enumerate(pairs):
        y = 28 + index * 42
        width = max(18, int((value / max_value) * 260))
        rows.append(
            f"""
            <text x="0" y="{y}" dominant-baseline="middle">{escape(shorten_text(label, 20))}</text>
            <rect x="130" y="{y - 10}" width="260" height="16" rx="8" fill="#e2e8f0"></rect>
            <rect x="130" y="{y - 10}" width="{width}" height="16" rx="8" fill="{color}"></rect>
            <text x="400" y="{y}" dominant-baseline="middle">{escape(formatter(value))}</text>
            """
        )
    height = 42 * len(pairs) + 24
    return f"<div class='chart-title'>{escape(title)}</div><svg viewBox='0 0 520 {height}' width='100%' height='{height}'>{''.join(rows)}</svg>"


def _build_svg_priority_chart(title: str, labels: list[Any], values: list[Any]) -> str:
    pairs = [(str(label), float(value)) for label, value in zip(labels, values) if label not in (None, "") and pd.notna(value)]
    if not pairs:
        return f"<div class='chart-title'>{escape(title)}</div><p class='muted'>Нет данных для визуализации.</p>"
    colors = {
        "Критический": "#dc2626",
        "Высокий": "#dc2626",
        "Средний": "#f59e0b",
        "Низкий": "#64748b",
        "Информация": "#0f766e",
    }
    max_value = max(value for _, value in pairs) or 1
    rows = []
    for index, (label, value) in enumerate(pairs):
        y = 28 + index * 42
        width = max(18, int((value / max_value) * 260))
        color = colors.get(label, "#64748b")
        rows.append(
            f"""
            <text x="0" y="{y}" dominant-baseline="middle">{escape(shorten_text(label, 20))}</text>
            <rect x="130" y="{y - 10}" width="260" height="16" rx="8" fill="#e2e8f0"></rect>
            <rect x="130" y="{y - 10}" width="{width}" height="16" rx="8" fill="{color}"></rect>
            <text x="400" y="{y}" dominant-baseline="middle">{int(value)} SKU</text>
            """
        )
    height = 42 * len(pairs) + 24
    return f"<div class='chart-title'>{escape(title)}</div><svg viewBox='0 0 520 {height}' width='100%' height='{height}'>{''.join(rows)}</svg>"


def _build_svg_line_chart(points: list[tuple[str, float]], *, title: str, color: str) -> str:
    if not points:
        return f"<div class='chart-title'>{escape(title)}</div><p class='muted'>Нет данных для визуализации.</p>"
    values = [value for _, value in points]
    max_value = max(values) or 1
    min_value = min(values)
    spread = max(max_value - min_value, 1)
    coords = []
    for index, (_, value) in enumerate(points):
        x = 24 + index * (420 / max(1, len(points) - 1))
        y = 160 - ((value - min_value) / spread) * 120
        coords.append((x, y))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    dots = "".join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' fill='{color}'></circle>" for x, y in coords)
    labels = "".join(
        f"<text x='{coords[index][0]:.1f}' y='188' text-anchor='middle'>{escape(label)}</text>"
        for index, (label, _) in enumerate(points)
    )
    return f"""
    <div class='chart-title'>{escape(title)}</div>
    <svg viewBox='0 0 470 200' width='100%' height='200'>
      <rect x='20' y='20' width='430' height='150' rx='18' fill='#f8fafc' stroke='#e2e8f0'></rect>
      <polyline fill='none' stroke='{color}' stroke-width='3' points='{polyline}'></polyline>
      {dots}
      {labels}
    </svg>
    """


def _prepare_forecast_points(df: pd.DataFrame | None) -> list[tuple[str, float]]:
    if df is None or df.empty:
        return []
    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    prepared = (
        prepared.dropna(subset=["date"])
        .groupby("date", as_index=False)
        .agg(predicted_quantity=("predicted_quantity", "sum"))
        .sort_values("date")
        .head(10)
    )
    return [(row["date"].strftime("%d.%m"), float(row["predicted_quantity"])) for _, row in prepared.iterrows()]


def _prepare_daily_sales_points(df: pd.DataFrame | None) -> list[tuple[str, float]]:
    if df is None or df.empty:
        return []
    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    prepared = (
        prepared.dropna(subset=["date"])
        .groupby("date", as_index=False)
        .agg(revenue=("revenue", "sum"))
        .sort_values("date")
        .head(14)
    )
    return [(row["date"].strftime("%d.%m"), float(row["revenue"])) for _, row in prepared.iterrows()]


def _format_money(value: Any) -> str:
    text = format_money_text(value)
    return "—" if text == "Нет данных" else text


def _format_units(value: Any) -> str:
    text = format_quantity_text(value)
    return "—" if text == "Нет данных" else text


def _format_days(value: Any) -> str:
    text = format_days_text(value)
    return "—" if text == "Нет данных" else text


def _format_percent_like(value: Any) -> str:
    return format_percent_text(value)


def _format_ratio(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "Нет данных"
    if abs(number) <= 1:
        number *= 100
    return f"{number:,.1f}%".replace(",", " ").replace(".", ",")
