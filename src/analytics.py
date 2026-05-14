import pandas as pd


def calculate_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Считает основные сводные показатели бизнеса.
    """
    total_revenue = float(df["revenue"].sum())
    total_units_sold = int(df["quantity_sold"].sum())

    unique_products = int(df["sku"].nunique())
    unique_categories = int(df["category"].nunique()) if "category" in df.columns else 0

    average_revenue_per_sale_row = total_revenue / len(df) if len(df) > 0 else 0

    average_price_per_unit = total_revenue / total_units_sold if total_units_sold > 0 else 0

    metrics = {
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": total_units_sold,
        "unique_products": unique_products,
        "unique_categories": unique_categories,
        "average_revenue_per_sale_row": round(average_revenue_per_sale_row, 2),
        "average_price_per_unit": round(average_price_per_unit, 2),
        "date_range_days": int((df["date"].max() - df["date"].min()).days + 1) if len(df) > 0 else 0,
    }

    if "purchase_price" in df.columns:
        df_with_margin = df.copy()
        df_with_margin["purchase_price"] = pd.to_numeric(
            df_with_margin["purchase_price"],
            errors="coerce",
        )

        df_with_margin["gross_profit"] = (
            df_with_margin["revenue"]
            - df_with_margin["quantity_sold"] * df_with_margin["purchase_price"]
        )

        gross_profit = float(df_with_margin["gross_profit"].sum())

        gross_margin_percent = gross_profit / total_revenue * 100 if total_revenue > 0 else 0

        metrics["gross_profit"] = round(gross_profit, 2)
        metrics["gross_margin_percent"] = round(gross_margin_percent, 2)

    average_stock = float(pd.to_numeric(df["stock_on_hand"], errors="coerce").mean())
    metrics["inventory_turnover_ratio"] = round(
        total_units_sold / average_stock if average_stock > 0 else 0.0,
        2,
    )

    return metrics


def calculate_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Считает продажи по дням.
    """
    daily_sales = (
        df.groupby("date", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            quantity_sold=("quantity_sold", "sum"),
        )
        .sort_values("date")
    )

    return daily_sales


def calculate_product_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Считает продажи и остатки по товарам.
    """
    agg_dict = {
        "product_name": ("product_name", "first"),
        "category": ("category", "first"),
        "total_quantity_sold": ("quantity_sold", "sum"),
        "total_revenue": ("revenue", "sum"),
        "current_stock": ("stock_on_hand", "last"),
    }

    if "purchase_price" in df.columns:
        agg_dict["purchase_price"] = ("purchase_price", "last")

    if "selling_price" in df.columns:
        agg_dict["selling_price"] = ("selling_price", "last")

    product_sales = df.sort_values("date").groupby("sku", as_index=False).agg(**agg_dict)

    product_sales["average_daily_sales"] = product_sales.apply(
        lambda row: _calculate_average_daily_sales(df, row["sku"]),
        axis=1,
    )

    product_sales["stock_days_left"] = product_sales.apply(
        lambda row: _calculate_stock_days_left(
            current_stock=row["current_stock"],
            average_daily_sales=row["average_daily_sales"],
        ),
        axis=1,
    )

    product_sales = product_sales.sort_values(
        "total_revenue",
        ascending=False,
    )

    return product_sales


def calculate_category_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Считает продажи по категориям.
    """
    category_sales = (
        df.groupby("category", as_index=False)
        .agg(
            total_quantity_sold=("quantity_sold", "sum"),
            total_revenue=("revenue", "sum"),
            unique_products=("sku", "nunique"),
            average_stock_on_hand=("stock_on_hand", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    category_sales["inventory_turnover_ratio"] = category_sales.apply(
        lambda row: round(
            float(row["total_quantity_sold"] / row["average_stock_on_hand"])
            if row["average_stock_on_hand"] > 0
            else 0.0,
            2,
        ),
        axis=1,
    )

    return category_sales


def get_top_products_by_revenue(
    product_sales: pd.DataFrame,
    limit: int = 5,
) -> pd.DataFrame:
    """
    Возвращает топ товаров по выручке.
    """
    return product_sales.head(limit)


def get_low_stock_products(
    product_sales: pd.DataFrame,
    threshold_days: int = 7,
) -> pd.DataFrame:
    """
    Возвращает товары, запаса которых хватит меньше заданного количества дней.
    """
    low_stock_products = product_sales[product_sales["stock_days_left"] <= threshold_days].copy()

    return low_stock_products.sort_values("stock_days_left")


def get_overstock_products(
    product_sales: pd.DataFrame,
    threshold_days: int = 60,
) -> pd.DataFrame:
    """
    Возвращает товары, у которых слишком большой запас.
    """
    overstock_products = product_sales[product_sales["stock_days_left"] >= threshold_days].copy()

    return overstock_products.sort_values("stock_days_left", ascending=False)


def _calculate_average_daily_sales(
    df: pd.DataFrame,
    sku: str,
) -> float:
    product_df = df[df["sku"] == sku].copy()

    if product_df.empty:
        return 0.0

    min_date = product_df["date"].min()
    max_date = product_df["date"].max()

    days_count = (max_date - min_date).days + 1

    if days_count <= 0:
        return 0.0

    total_quantity = product_df["quantity_sold"].sum()

    return round(float(total_quantity / days_count), 2)


def _calculate_stock_days_left(
    current_stock: float,
    average_daily_sales: float,
) -> float:
    if average_daily_sales <= 0:
        return float("inf")

    return round(float(current_stock / average_daily_sales), 1)
