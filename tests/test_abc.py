from src.api.abc import build_abc_analysis, build_abc_summary


def test_build_abc_analysis_returns_empty_list_for_empty_input():
    result = build_abc_analysis([])

    assert result == []


def test_build_abc_analysis_assigns_classes():
    top_products = [
        {
            "sku": "A-001",
            "product_name": "Товар A",
            "category": "Категория 1",
            "total_revenue": 800,
            "total_quantity_sold": 10,
        },
        {
            "sku": "B-001",
            "product_name": "Товар B",
            "category": "Категория 1",
            "total_revenue": 150,
            "total_quantity_sold": 5,
        },
        {
            "sku": "C-001",
            "product_name": "Товар C",
            "category": "Категория 2",
            "total_revenue": 50,
            "total_quantity_sold": 2,
        },
    ]

    result = build_abc_analysis(top_products)

    assert len(result) == 3

    assert result[0]["sku"] == "A-001"
    assert result[0]["abc_class"] == "A"
    assert result[0]["revenue_share_percent"] == 80
    assert result[0]["cumulative_share_percent"] == 80

    assert result[1]["sku"] == "B-001"
    assert result[1]["abc_class"] == "B"
    assert result[1]["revenue_share_percent"] == 15
    assert result[1]["cumulative_share_percent"] == 95

    assert result[2]["sku"] == "C-001"
    assert result[2]["abc_class"] == "C"
    assert result[2]["revenue_share_percent"] == 5
    assert result[2]["cumulative_share_percent"] == 100


def test_build_abc_analysis_sorts_by_revenue_desc():
    top_products = [
        {
            "sku": "LOW",
            "product_name": "Малый товар",
            "category": "Категория",
            "total_revenue": 100,
            "total_quantity_sold": 1,
        },
        {
            "sku": "HIGH",
            "product_name": "Большой товар",
            "category": "Категория",
            "total_revenue": 900,
            "total_quantity_sold": 9,
        },
    ]

    result = build_abc_analysis(top_products)

    assert result[0]["sku"] == "HIGH"
    assert result[1]["sku"] == "LOW"


def test_build_abc_analysis_handles_zero_revenue():
    top_products = [
        {
            "sku": "ZERO-001",
            "product_name": "Нулевой товар 1",
            "category": "Категория",
            "total_revenue": 0,
            "total_quantity_sold": 0,
        },
        {
            "sku": "ZERO-002",
            "product_name": "Нулевой товар 2",
            "category": "Категория",
            "total_revenue": 0,
            "total_quantity_sold": 0,
        },
    ]

    result = build_abc_analysis(top_products)

    assert len(result) == 2

    for item in result:
        assert item["abc_class"] == "C"
        assert item["revenue_share_percent"] == 0
        assert item["cumulative_share_percent"] == 0


def test_build_abc_summary_counts_products_and_revenue():
    abc_analysis = [
        {
            "sku": "A-001",
            "product_name": "Товар A",
            "category": "Категория",
            "total_revenue": 800,
            "total_quantity_sold": 10,
            "revenue_share_percent": 80,
            "cumulative_share_percent": 80,
            "abc_class": "A",
            "abc_description": "Ключевой товар.",
        },
        {
            "sku": "B-001",
            "product_name": "Товар B",
            "category": "Категория",
            "total_revenue": 150,
            "total_quantity_sold": 5,
            "revenue_share_percent": 15,
            "cumulative_share_percent": 95,
            "abc_class": "B",
            "abc_description": "Средний вклад.",
        },
        {
            "sku": "C-001",
            "product_name": "Товар C",
            "category": "Категория",
            "total_revenue": 50,
            "total_quantity_sold": 2,
            "revenue_share_percent": 5,
            "cumulative_share_percent": 100,
            "abc_class": "C",
            "abc_description": "Низкий вклад.",
        },
    ]

    summary = build_abc_summary(abc_analysis)

    assert summary["A"]["products_count"] == 1
    assert summary["A"]["total_revenue"] == 800
    assert summary["A"]["revenue_share_percent"] == 80

    assert summary["B"]["products_count"] == 1
    assert summary["B"]["total_revenue"] == 150
    assert summary["B"]["revenue_share_percent"] == 15

    assert summary["C"]["products_count"] == 1
    assert summary["C"]["total_revenue"] == 50
    assert summary["C"]["revenue_share_percent"] == 5
