from pathlib import Path

import pandas as pd

from src.load_data import load_sales_data


def test_load_sales_data_csv(tmp_path: Path):
    input_file = tmp_path / "sales.csv"

    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": 5,
                "revenue": 2100,
                "stock_on_hand": 120,
            }
        ]
    )

    df.to_csv(input_file, index=False)

    loaded_df = load_sales_data(input_file)

    assert len(loaded_df) == 1
    assert "sku" in loaded_df.columns
    assert loaded_df.loc[0, "sku"] == "COF-001"


def test_load_sales_data_xlsx(tmp_path: Path):
    input_file = tmp_path / "sales.xlsx"

    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": 5,
                "revenue": 2100,
                "stock_on_hand": 120,
            }
        ]
    )

    df.to_excel(input_file, index=False)

    loaded_df = load_sales_data(input_file)

    assert len(loaded_df) == 1
    assert "sku" in loaded_df.columns
    assert loaded_df.loc[0, "sku"] == "COF-001"
