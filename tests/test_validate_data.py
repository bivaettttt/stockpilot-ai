import pandas as pd

from src.validate_data import prepare_sales_data, validate_sales_data


def test_validate_sales_data_success():
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
            }
        ]
    )

    is_valid, errors = validate_sales_data(df)

    assert is_valid is True
    assert errors == []


def test_validate_sales_data_missing_required_column():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": 5,
                "stock_on_hand": 120,
            }
        ]
    )

    is_valid, errors = validate_sales_data(df)

    assert is_valid is False
    assert any("Не хватает обязательных колонок" in error for error in errors)


def test_validate_sales_data_negative_values():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": -5,
                "revenue": 2100,
                "stock_on_hand": 120,
            }
        ]
    )

    is_valid, errors = validate_sales_data(df)

    assert is_valid is False
    assert any("отрицательные значения" in error for error in errors)


def test_validate_sales_data_duplicate_date_sku():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": 5,
                "revenue": 2100,
                "stock_on_hand": 120,
            },
            {
                "date": "2026-01-01",
                "sku": "COF-001",
                "product_name": "Кофе арабика 250г",
                "quantity_sold": 4,
                "revenue": 1680,
                "stock_on_hand": 116,
            },
        ]
    )

    is_valid, errors = validate_sales_data(df)

    assert is_valid is False
    assert any("дубли" in error.lower() for error in errors)


def test_prepare_sales_data_adds_optional_columns():
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

    prepared_df = prepare_sales_data(df)

    assert "category" in prepared_df.columns
    assert "purchase_price" in prepared_df.columns
    assert "selling_price" in prepared_df.columns
    assert "supplier" in prepared_df.columns
    assert "promotion_flag" in prepared_df.columns
    assert prepared_df.loc[0, "category"] == "Без категории"
