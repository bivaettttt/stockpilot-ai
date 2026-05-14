from pathlib import Path

import pandas as pd

from src.config import AppConfig
from src.pipeline import run_stockpilot_pipeline


def test_run_stockpilot_pipeline_creates_outputs(tmp_path: Path):
    input_file = tmp_path / "sales.csv"
    output_file = tmp_path / "report.xlsx"
    dashboard_file = tmp_path / "dashboard.html"

    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "category": "Кофе",
                "quantity_sold": 5,
                "revenue": 2100,
                "stock_on_hand": 120,
                "purchase_price": 250,
                "selling_price": 420,
            },
            {
                "date": "2026-01-02",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "category": "Кофе",
                "quantity_sold": 6,
                "revenue": 2520,
                "stock_on_hand": 114,
                "purchase_price": 250,
                "selling_price": 420,
            },
            {
                "date": "2026-01-01",
                "sku": "TEA-001",
                "product_name": "Чай зелёный 100г",
                "category": "Чай",
                "quantity_sold": 3,
                "revenue": 990,
                "stock_on_hand": 80,
                "purchase_price": 160,
                "selling_price": 330,
            },
            {
                "date": "2026-01-02",
                "sku": "TEA-001",
                "product_name": "Чай зелёный 100г",
                "category": "Чай",
                "quantity_sold": 4,
                "revenue": 1320,
                "stock_on_hand": 76,
                "purchase_price": 160,
                "selling_price": 330,
            },
        ]
    )

    df.to_csv(input_file, index=False)

    config = AppConfig(
        input_file=input_file,
        output_file=output_file,
        dashboard_file=dashboard_file,
        forecast_horizon_days=14,
        safety_stock_percent=0.2,
        supply_lead_time_days=3,
    )

    result = run_stockpilot_pipeline(config)

    assert result.report_path.exists()
    assert result.dashboard_path.exists()
    assert result.summary_metrics["total_revenue"] == 6930
    assert len(result.recommendations) > 0
    assert len(result.product_forecast) > 0
    assert "forecast_quality" in result.analysis_reliability
