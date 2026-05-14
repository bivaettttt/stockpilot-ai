import pandas as pd

from src.forecast import build_product_forecast
from src.services.reliability_service import build_analysis_reliability


def test_build_analysis_reliability_returns_metrics_for_stable_series():
    df = pd.DataFrame(
        [
            {
                "date": f"2026-01-{day:02d}",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "category": "Кофе",
                "quantity_sold": 5,
                "revenue": 2100,
                "stock_on_hand": 100,
                "promotion_flag": False,
            }
            for day in range(1, 29)
        ]
    )

    product_forecast = build_product_forecast(df, horizon_days=7)
    reliability = build_analysis_reliability(
        prepared_df=df,
        product_forecast=product_forecast,
        data_quality={
            "completeness_score": 95,
            "validity_score": 94,
            "consistency_score": 96,
            "warnings_count": 0,
            "errors_count": 0,
        },
        horizon_days=7,
    )

    assert reliability["forecast_quality"]["wape"] is not None
    assert reliability["forecast_quality"]["mae"] is not None
    assert reliability["forecast_quality"]["bias"] is not None
    assert reliability["forecast_quality"]["overall_confidence"] in {"high", "medium"}
    assert reliability["sku_reliability"][0]["wape"] is not None


def test_build_analysis_reliability_marks_insufficient_history():
    df = pd.DataFrame(
        [
            {
                "date": f"2026-01-0{day}",
                "sku": "TEA-001",
                "product_name": "Чай зелёный 100г",
                "category": "Чай",
                "quantity_sold": 2,
                "revenue": 660,
                "stock_on_hand": 40,
            }
            for day in range(1, 5)
        ]
    )

    product_forecast = build_product_forecast(df, horizon_days=7)
    reliability = build_analysis_reliability(
        prepared_df=df,
        product_forecast=product_forecast,
        data_quality={
            "completeness_score": 90,
            "validity_score": 90,
            "consistency_score": 90,
            "warnings_count": 0,
            "errors_count": 0,
        },
        horizon_days=7,
    )

    sku_item = reliability["sku_reliability"][0]
    assert sku_item["confidence"] == "insufficient_data"
    assert sku_item["wape"] is None
    assert sku_item["reason"] == "Недостаточно истории"


def test_build_analysis_reliability_adds_stockout_warning():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "MIL-001",
                "product_name": "Молоко 1л",
                "category": "Молоко",
                "quantity_sold": 4,
                "revenue": 320,
                "stock_on_hand": 12,
                "promotion_flag": False,
            },
            {
                "date": "2026-01-02",
                "sku": "MIL-001",
                "product_name": "Молоко 1л",
                "category": "Молоко",
                "quantity_sold": 0,
                "revenue": 0,
                "stock_on_hand": 0,
                "promotion_flag": False,
            },
            {
                "date": "2026-01-03",
                "sku": "MIL-001",
                "product_name": "Молоко 1л",
                "category": "Молоко",
                "quantity_sold": 5,
                "revenue": 400,
                "stock_on_hand": 10,
                "promotion_flag": False,
            },
        ]
    )

    product_forecast = build_product_forecast(df, horizon_days=3)
    reliability = build_analysis_reliability(
        prepared_df=df,
        product_forecast=product_forecast,
        data_quality={
            "completeness_score": 90,
            "validity_score": 90,
            "consistency_score": 90,
            "warnings_count": 0,
            "errors_count": 0,
        },
        horizon_days=3,
    )

    assert any(
        warning["code"] == "possible_stockout_censored_demand"
        for warning in reliability["warnings"]
    )


def test_build_analysis_reliability_adds_promo_warning():
    df = pd.DataFrame(
        [
            {
                "date": f"2026-01-{day:02d}",
                "sku": "SNK-001",
                "product_name": "Батончик",
                "category": "Снеки",
                "quantity_sold": 8 if day % 2 else 3,
                "revenue": 80 if day % 2 else 30,
                "stock_on_hand": 50,
                "promotion_flag": day <= 10,
            }
            for day in range(1, 21)
        ]
    )

    product_forecast = build_product_forecast(df, horizon_days=5)
    reliability = build_analysis_reliability(
        prepared_df=df,
        product_forecast=product_forecast,
        data_quality={
            "completeness_score": 90,
            "validity_score": 90,
            "consistency_score": 90,
            "warnings_count": 0,
            "errors_count": 0,
        },
        horizon_days=5,
    )

    assert any(
        warning["code"] == "promotion_periods_can_distort_forecast"
        for warning in reliability["warnings"]
    )
