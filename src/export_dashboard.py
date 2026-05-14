from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from src.report_presenter import (
    build_abc_xyz_export_df,
    build_abc_xyz_summary_df,
    build_business_purchase_plan_df,
    build_reliability_distribution_df,
    build_top_risks_df,
    format_days_text,
    format_money_text,
    format_percent_text,
    format_quantity_text,
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

    period = _build_period_text(daily_sales)
    generated_text = pd.to_datetime(generated_at or pd.Timestamp.now()).strftime("%d.%m.%Y %H:%M")
    executive = insights[0] if insights else _default_executive_text(purchase_plan, analysis_reliability)

    total_revenue = summary_metrics.get("total_revenue", 0)
    total_units = summary_metrics.get("total_units_sold", 0)
    sku_count = summary_metrics.get("unique_products", 0)
    procurement_units = int(purchase_plan["Итоговое количество"].sum()) if not purchase_plan.empty else 0
    reliability = analysis_reliability.get("forecast_quality", {}) or {}
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
    forecast_chart = _build_svg_line_chart(_prepare_forecast_points(daily_forecast_chart_data))
    reliability_chart = _build_svg_bar_chart(
        title="Распределение надёжности SKU",
        labels=list(reliability_distribution.get("Надёжность", pd.Series(dtype=str))),
        values=list(reliability_distribution.get("SKU", pd.Series(dtype=float))),
        formatter=lambda value: f"{int(value)} SKU",
        color="#7c3aed",
    )
    abc_chart = _build_svg_bar_chart(
        title="Распределение ABC/XYZ",
        labels=list(abc_summary_df.get("Класс", pd.Series(dtype=str))),
        values=list(abc_summary_df.get("SKU", pd.Series(dtype=float))),
        formatter=lambda value: f"{int(value)} SKU",
        color="#f59e0b",
    )

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
    main {{ max-width: 1440px; margin: 0 auto; padding: 32px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 24px;
      padding: 28px;
      border-radius: 34px;
      background: linear-gradient(160deg, rgba(255,255,255,0.94), rgba(248,250,252,0.9));
      border: 1px solid rgba(219,227,239,0.88);
      box-shadow: var(--shadow);
    }}
    .hero h1 {{ margin: 0; font-size: 38px; line-height: 1.02; }}
    .hero p {{ margin: 10px 0 0; color: var(--muted); line-height: 1.6; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      align-content: start;
    }}
    .meta-card, .card {{
      border-radius: var(--radius);
      background: var(--surface);
      border: 1px solid rgba(219,227,239,0.9);
      box-shadow: var(--shadow);
    }}
    .meta-card {{ padding: 16px 18px; }}
    .meta-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
    .meta-value {{ margin-top: 6px; font-weight: 700; }}
    .badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;
      background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;
    }}
    .grid {{ display: grid; gap: 20px; margin-top: 22px; }}
    .kpis {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .two {{ grid-template-columns: 1.08fr 0.92fr; }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .card {{ padding: 22px; }}
    .card h2 {{ margin: 0 0 6px; font-size: 19px; }}
    .eyebrow {{ color: var(--muted); font-size: 13px; margin-bottom: 14px; }}
    .kpi-label {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
    .kpi-value {{ font-size: 30px; font-weight: 800; margin-bottom: 8px; }}
    .kpi-note {{ color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .stack {{ display: grid; gap: 12px; }}
    .list-item {{
      display: grid; grid-template-columns: 26px 1fr; gap: 12px;
      padding: 14px; border-radius: 18px; background: var(--surface-2); border: 1px solid var(--line);
    }}
    .list-index {{
      width: 26px; height: 26px; border-radius: 999px; display: grid; place-items: center;
      font-weight: 700; background: #dbeafe; color: #1d4ed8;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th {{ text-align: left; color: var(--muted); font-weight: 700; padding: 12px 10px; border-bottom: 1px solid var(--line); white-space: nowrap; }}
    td {{ padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    .tag {{
      display: inline-flex; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
    }}
    .critical {{ background: #fee2e2; color: #991b1b; }}
    .high {{ background: #fef3c7; color: #92400e; }}
    .medium {{ background: #dbeafe; color: #1d4ed8; }}
    .low {{ background: #e2e8f0; color: #334155; }}
    .info {{ background: #dcfce7; color: #166534; }}
    .muted {{ color: var(--muted); }}
    .chart-card {{ padding: 18px; border-radius: 22px; background: var(--surface-2); border: 1px solid var(--line); }}
    .chart-title {{ font-size: 14px; font-weight: 700; margin-bottom: 10px; }}
    svg text {{ font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #475569; font-size: 12px; }}
    .footer {{ margin-top: 26px; text-align: center; color: var(--muted); font-size: 13px; }}
    @media print {{
      body {{ background: white; }}
      main {{ padding: 10mm; }}
      .hero, .card, .meta-card {{ box-shadow: none; }}
      .grid, .hero {{ break-inside: avoid; }}
    }}
    @media (max-width: 1080px) {{
      .hero, .kpis, .two, .three {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 760px) {{
      main {{ padding: 18px; }}
      .hero, .kpis, .two, .three, .meta {{ grid-template-columns: 1fr; }}
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
        <p>Отчёт по продажам, запасам, закупочным решениям и надёжности прогноза. Подходит для обсуждения с владельцем бизнеса или командой закупок.</p>
        <div class="card" style="margin-top:18px; padding:18px 20px;">
          <div class="eyebrow">Управленческая сводка</div>
          <div style="font-size:16px; line-height:1.6;">{escape(executive)}</div>
        </div>
      </div>
      <div class="meta">
        <div class="meta-card"><div class="meta-label">Файл</div><div class="meta-value">{escape(source_filename or "Файл анализа")}</div></div>
        <div class="meta-card"><div class="meta-label">Дата анализа</div><div class="meta-value">{generated_text}</div></div>
        <div class="meta-card"><div class="meta-label">Период</div><div class="meta-value">{escape(period)}</div></div>
        <div class="meta-card"><div class="meta-label">SKU / строк</div><div class="meta-value">{int(sku_count)} / {int((data_quality or {}).get("total_rows", 0) or 0)}</div></div>
        <div class="meta-card"><div class="meta-label">Горизонт прогноза</div><div class="meta-value">{int(parameters.get("horizon", 0) or 0)} дн.</div></div>
        <div class="meta-card"><div class="meta-label">Источник</div><div class="meta-value">StockPilot AI</div></div>
      </div>
    </section>

    <section class="grid kpis">
      {_kpi_card("Выручка", _format_money(total_revenue), "Фактическая выручка за анализируемый период")}
      {_kpi_card("Продано единиц", _format_units(total_units), "Суммарный объём продаж")}
      {_kpi_card("SKU в анализе", f"{int(sku_count)}", "Товары, которые вошли в расчёт")}
      {_kpi_card("К закупке", _format_units(procurement_units), "Сумма по business-facing закупочному плану")}
      {_kpi_card("Качество данных", _format_percent_like(data_quality_score), "Полнота входного файла")}
      {_kpi_card("Надёжность прогноза", str(localize_value(reliability.get("overall_confidence")) or "Нет данных"), "Честная оценка без обещаний точности")}
      {_kpi_card("WAPE", _format_ratio(reliability.get("wape")), "Средняя относительная ошибка прогноза")}
      {_kpi_card("Bias", _format_ratio(reliability.get("bias")), "Смещение: завышает или занижает спрос")}
    </section>

    <section class="grid two">
      <article class="card">
        <h2>Что сделать в первую очередь</h2>
        <div class="eyebrow">Практические действия по текущему анализу</div>
        <div class="stack">
          {_render_action_list(_build_actions(purchase_plan, top_risks, analysis_reliability))}
        </div>
      </article>
      <article class="card">
        <h2>Что проверить вручную</h2>
        <div class="eyebrow">Ограничения прогноза и качества данных</div>
        <div class="stack">
          {_render_action_list(_build_checks(data_quality, analysis_reliability))}
        </div>
      </article>
    </section>

    <section class="grid two">
      <article class="card">
        <h2>Продажи и выручка</h2>
        <div class="eyebrow">Категории, товары и спрос</div>
        <div class="chart-card">{category_chart}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{top_products_chart}</div>
      </article>
      <article class="card">
        <h2>Надёжность прогноза</h2>
        <div class="eyebrow">Надёжность прогноза и SKU, которые стоит проверить</div>
        <div class="chart-card">{reliability_chart}</div>
        <div style="height:14px;"></div>
        <div class="chart-card">{forecast_chart}</div>
      </article>
    </section>

    <section class="grid two">
      <article class="card">
        <h2>Закупочный план</h2>
        <div class="eyebrow">Короткая business-facing таблица по закупке</div>
        <div class="table-wrap">{_render_purchase_plan_table(purchase_plan)}</div>
      </article>
      <article class="card">
        <h2>Risks</h2>
        <div class="eyebrow">Очередь рисков и конкретные действия</div>
        <div class="table-wrap">{_render_risk_table(top_risks)}</div>
      </article>
    </section>

    <section class="grid two">
      <article class="card">
        <h2>ABC/XYZ</h2>
        <div class="eyebrow">Классы вклада в выручку и стабильности спроса</div>
        <div class="chart-card">{abc_chart}</div>
        <div style="height:14px;"></div>
        <div class="table-wrap">{_render_abc_table(abc_df)}</div>
      </article>
      <article class="card">
        <h2>Качество данных</h2>
        <div class="eyebrow">Что влияет на интерпретацию отчёта</div>
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

    <div class="footer">Сформировано StockPilot AI. Исходный файл анализируется системой; AI-пояснения, если используются, формируются только по компактному контексту анализа.</div>
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


def _default_executive_text(purchase_plan: pd.DataFrame, analysis_reliability: dict[str, Any]) -> str:
    to_buy = int(purchase_plan["Итоговое количество"].sum()) if not purchase_plan.empty else 0
    low_confidence = sum(
        1
        for item in (analysis_reliability.get("sku_reliability", []) or [])
        if item.get("confidence") == "low"
    )
    return (
        f"В текущем анализе к закупке рекомендуется {to_buy} ед. по ключевым позициям. "
        f"SKU с низкой надёжностью прогноза: {low_confidence}. "
        "Начните с приоритетных товаров и проверьте ограничения по данным перед подтверждением заказа."
    )


def _kpi_card(label: str, value: str, note: str) -> str:
    return f"""
    <div class="card">
      <div class="kpi-label">{escape(label)}</div>
      <div class="kpi-value">{escape(value)}</div>
      <div class="kpi-note">{escape(note)}</div>
    </div>
    """


def _render_action_list(items: list[str]) -> str:
    return "".join(
        f"<div class='list-item'><div class='list-index'>{index}</div><div>{escape(item)}</div></div>"
        for index, item in enumerate(items, start=1)
    )


def _build_actions(purchase_plan: pd.DataFrame, top_risks: pd.DataFrame, analysis_reliability: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not purchase_plan.empty:
        for _, row in purchase_plan[purchase_plan["Итоговое количество"] > 0].head(3).iterrows():
            actions.append(f"{row['SKU']} — {row['Товар']}: {row['Причина'] or 'Проверьте покрытие и спрос вручную.'}")
    if not top_risks.empty:
        for _, row in top_risks.head(2).iterrows():
            actions.append(f"Проверьте риск по {row['SKU']}: {row['Действие']}.")
    if not actions:
        actions.append("Критичных закупок не найдено. Сфокусируйтесь на рисках и качестве данных.")
    if (analysis_reliability.get("forecast_quality", {}) or {}).get("overall_confidence") == "low":
        actions.append("Надёжность прогноза низкая: ключевые SKU стоит проверить вручную перед закупкой.")
    return actions[:5]


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
              <td>{escape(shorten_text(row['Причина'], 88))}</td>
            </tr>
            """
        )
    return f"""
    <table>
      <thead><tr><th>SKU</th><th>Товар</th><th>Приоритет</th><th>Остаток</th><th>Покрытие</th><th>К заказу</th><th>Причина</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


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


def _build_svg_line_chart(points: list[tuple[str, float]]) -> str:
    if not points:
        return "<div class='chart-title'>Прогноз спроса по дням</div><p class='muted'>Нет данных для графика прогноза.</p>"
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
    dots = "".join(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' fill='#7c3aed'></circle>" for x, y in coords)
    labels = "".join(
        f"<text x='{coords[index][0]:.1f}' y='188' text-anchor='middle'>{escape(label)}</text>"
        for index, (label, _) in enumerate(points)
    )
    return f"""
    <div class='chart-title'>Прогноз спроса по дням</div>
    <svg viewBox='0 0 470 200' width='100%' height='200'>
      <rect x='20' y='20' width='430' height='150' rx='18' fill='#f8fafc' stroke='#e2e8f0'></rect>
      <polyline fill='none' stroke='#7c3aed' stroke-width='3' points='{polyline}'></polyline>
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
