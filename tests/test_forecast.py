import pandas as pd

from src.forecast import build_daily_forecast_chart_data, build_product_forecast


def test_build_product_forecast_returns_model_metadata():
    df = pd.DataFrame(
        [
            {
                "date": f"2026-01-{day:02d}",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "category": "Кофе",
                "quantity_sold": 2 + (day % 3),
                "revenue": (2 + (day % 3)) * 420,
                "stock_on_hand": 100 - day,
                "selling_price": 420,
            }
            for day in range(1, 22)
        ]
    )

    forecast = build_product_forecast(df, horizon_days=14)

    assert not forecast.empty
    assert "forecast_model" in forecast.columns
    assert "confidence_score" in forecast.columns
    assert "demand_pattern" in forecast.columns
    assert forecast.iloc[0]["predicted_quantity"] > 0


def test_build_daily_forecast_chart_data_keeps_forecast_model():
    df = pd.DataFrame(
        [
            {
                "date": f"2026-01-{day:02d}",
                "sku": "TEA-001",
                "product_name": "Чай зелёный 100г",
                "category": "Чай",
                "quantity_sold": 1 if day % 4 else 0,
                "revenue": 330 if day % 4 else 0,
                "stock_on_hand": 60,
                "selling_price": 330,
            }
            for day in range(1, 18)
        ]
    )

    chart_data = build_daily_forecast_chart_data(df, horizon_days=7)

    assert len(chart_data) == 7
    assert "forecast_model" in chart_data.columns
