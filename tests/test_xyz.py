import pandas as pd

from src.api.xyz import build_xyz_analysis, build_xyz_summary


def test_build_xyz_analysis_returns_empty_list_for_empty_input():
    df = pd.DataFrame()

    result = build_xyz_analysis(df)

    assert result == []


def test_build_xyz_analysis_returns_empty_list_without_required_columns():
    df = pd.DataFrame(
        [
            {
                "sku": "COF-001",
                "product_name": "Кофе",
            }
        ]
    )

    result = build_xyz_analysis(df)

    assert result == []


def test_build_xyz_analysis_assigns_x_class_for_stable_demand():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе",
                "category": "Кофе",
                "quantity_sold": 10,
                "revenue": 1000,
            },
            {
                "date": "2026-01-02",
                "sku": "COF-001",
                "product_name": "Кофе",
                "category": "Кофе",
                "quantity_sold": 11,
                "revenue": 1100,
            },
            {
                "date": "2026-01-03",
                "sku": "COF-001",
                "product_name": "Кофе",
                "category": "Кофе",
                "quantity_sold": 10,
                "revenue": 1000,
            },
        ]
    )

    result = build_xyz_analysis(df)

    assert len(result) == 1
    assert result[0]["sku"] == "COF-001"
    assert result[0]["xyz_class"] == "X"
    assert result[0]["coefficient_of_variation"] <= 30


def test_build_xyz_analysis_assigns_y_class_for_moderately_unstable_demand():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "TEA-001",
                "product_name": "Чай",
                "category": "Чай",
                "quantity_sold": 10,
                "revenue": 1000,
            },
            {
                "date": "2026-01-02",
                "sku": "TEA-001",
                "product_name": "Чай",
                "category": "Чай",
                "quantity_sold": 20,
                "revenue": 2000,
            },
            {
                "date": "2026-01-03",
                "sku": "TEA-001",
                "product_name": "Чай",
                "category": "Чай",
                "quantity_sold": 10,
                "revenue": 1000,
            },
        ]
    )

    result = build_xyz_analysis(df)

    assert len(result) == 1
    assert result[0]["sku"] == "TEA-001"
    assert result[0]["xyz_class"] == "Y"
    assert 30 < result[0]["coefficient_of_variation"] <= 70


def test_build_xyz_analysis_assigns_z_class_for_chaotic_demand():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "SYR-001",
                "product_name": "Сироп",
                "category": "Сиропы",
                "quantity_sold": 1,
                "revenue": 100,
            },
            {
                "date": "2026-01-02",
                "sku": "SYR-001",
                "product_name": "Сироп",
                "category": "Сиропы",
                "quantity_sold": 30,
                "revenue": 3000,
            },
            {
                "date": "2026-01-03",
                "sku": "SYR-001",
                "product_name": "Сироп",
                "category": "Сиропы",
                "quantity_sold": 1,
                "revenue": 100,
            },
        ]
    )

    result = build_xyz_analysis(df)

    assert len(result) == 1
    assert result[0]["sku"] == "SYR-001"
    assert result[0]["xyz_class"] == "Z"
    assert result[0]["coefficient_of_variation"] > 70


def test_build_xyz_summary_counts_products_and_revenue():
    xyz_analysis = [
        {
            "sku": "COF-001",
            "product_name": "Кофе",
            "category": "Кофе",
            "total_revenue": 1000,
            "xyz_class": "X",
        },
        {
            "sku": "TEA-001",
            "product_name": "Чай",
            "category": "Чай",
            "total_revenue": 500,
            "xyz_class": "Y",
        },
        {
            "sku": "SYR-001",
            "product_name": "Сироп",
            "category": "Сиропы",
            "total_revenue": 500,
            "xyz_class": "Z",
        },
    ]

    summary = build_xyz_summary(xyz_analysis)

    assert summary["X"]["products_count"] == 1
    assert summary["X"]["total_revenue"] == 1000
    assert summary["X"]["revenue_share_percent"] == 50

    assert summary["Y"]["products_count"] == 1
    assert summary["Y"]["total_revenue"] == 500
    assert summary["Y"]["revenue_share_percent"] == 25

    assert summary["Z"]["products_count"] == 1
    assert summary["Z"]["total_revenue"] == 500
    assert summary["Z"]["revenue_share_percent"] == 25
