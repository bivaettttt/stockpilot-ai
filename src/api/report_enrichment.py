from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def enrich_excel_report_with_advanced_analytics(
    report_path: str | Path,
    abc_analysis: list[dict[str, Any]],
    xyz_analysis: list[dict[str, Any]],
    abc_xyz_matrix: list[dict[str, Any]],
) -> None:
    """
    Добавляет в существующий Excel-отчёт дополнительные листы:

    - ABC analysis
    - XYZ analysis
    - ABC XYZ matrix

    Используется на API-уровне после выполнения основного pipeline.
    """
    path = Path(report_path)

    if not path.exists():
        return

    sheets = {
        "ABC анализ": _build_abc_dataframe(abc_analysis),
        "XYZ анализ": _build_xyz_dataframe(xyz_analysis),
        "ABC XYZ матрица": _build_abc_xyz_dataframe(abc_xyz_matrix),
    }

    with pd.ExcelWriter(
        path,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
    ) as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook = writer.book
        for sheet_name in sheets:
            worksheet = workbook[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value or "")) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 12), 42)


def _build_abc_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "sku",
        "product_name",
        "category",
        "abc_class",
        "total_revenue",
        "total_quantity_sold",
        "revenue_share_percent",
        "cumulative_share_percent",
        "abc_description",
    ]

    return _records_to_dataframe(items, columns)


def _build_xyz_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "sku",
        "product_name",
        "category",
        "xyz_class",
        "observation_days",
        "total_revenue",
        "total_quantity_sold",
        "average_daily_demand",
        "demand_std",
        "coefficient_of_variation",
        "xyz_description",
    ]

    return _records_to_dataframe(items, columns)


def _build_abc_xyz_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "sku",
        "product_name",
        "category",
        "abc_class",
        "xyz_class",
        "abc_xyz_class",
        "management_priority",
        "total_revenue",
        "total_quantity_sold",
        "revenue_share_percent",
        "cumulative_share_percent",
        "average_daily_demand",
        "coefficient_of_variation",
        "management_action",
    ]

    return _records_to_dataframe(items, columns)


def _records_to_dataframe(
    items: list[dict[str, Any]],
    columns: list[str],
) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(items)

    for column in columns:
        if column not in df.columns:
            df[column] = None

    return df[columns]
