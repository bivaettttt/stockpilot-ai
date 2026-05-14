from src.api.portfolio import build_abc_xyz_matrix, build_abc_xyz_summary


def test_build_abc_xyz_matrix_combines_classes_by_sku():
    abc_analysis = [
        {
            "sku": "COF-001",
            "product_name": "Кофе",
            "category": "Кофе",
            "total_revenue": 1000,
            "total_quantity_sold": 10,
            "revenue_share_percent": 80,
            "cumulative_share_percent": 80,
            "abc_class": "A",
        }
    ]

    xyz_analysis = [
        {
            "sku": "COF-001",
            "product_name": "Кофе",
            "category": "Кофе",
            "average_daily_demand": 5,
            "coefficient_of_variation": 20,
            "xyz_class": "X",
        }
    ]

    matrix = build_abc_xyz_matrix(abc_analysis, xyz_analysis)

    assert len(matrix) == 1
    assert matrix[0]["sku"] == "COF-001"
    assert matrix[0]["abc_class"] == "A"
    assert matrix[0]["xyz_class"] == "X"
    assert matrix[0]["abc_xyz_class"] == "AX"
    assert matrix[0]["management_priority"] == "high"


def test_build_abc_xyz_matrix_ignores_missing_sku_in_xyz():
    abc_analysis = [
        {
            "sku": "COF-001",
            "product_name": "Кофе",
            "category": "Кофе",
            "total_revenue": 1000,
            "abc_class": "A",
        }
    ]

    xyz_analysis = [
        {
            "sku": "TEA-001",
            "product_name": "Чай",
            "category": "Чай",
            "xyz_class": "X",
        }
    ]

    matrix = build_abc_xyz_matrix(abc_analysis, xyz_analysis)

    assert matrix == []


def test_build_abc_xyz_summary_counts_classes():
    matrix = [
        {
            "sku": "COF-001",
            "abc_xyz_class": "AX",
            "total_revenue": 1000,
        },
        {
            "sku": "TEA-001",
            "abc_xyz_class": "CZ",
            "total_revenue": 250,
        },
    ]

    summary = build_abc_xyz_summary(matrix)

    assert summary["AX"]["products_count"] == 1
    assert summary["AX"]["total_revenue"] == 1000
    assert summary["AX"]["revenue_share_percent"] == 80
    assert summary["AX"]["management_priority"] == "high"

    assert summary["CZ"]["products_count"] == 1
    assert summary["CZ"]["total_revenue"] == 250
    assert summary["CZ"]["revenue_share_percent"] == 20
    assert summary["CZ"]["management_priority"] == "low"
