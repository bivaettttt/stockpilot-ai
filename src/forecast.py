import pandas as pd

from src.services.forecasting_service import (
    DEFAULT_FORECAST_HORIZON_DAYS,
    build_daily_forecast_chart_df,
    build_product_forecast_df,
    get_daily_demand_series,
)


def build_product_forecast(
    df: pd.DataFrame,
    horizon_days: int = DEFAULT_FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    return build_product_forecast_df(df, horizon_days=horizon_days)


def build_daily_forecast_chart_data(
    df: pd.DataFrame,
    horizon_days: int = DEFAULT_FORECAST_HORIZON_DAYS,
) -> pd.DataFrame:
    return build_daily_forecast_chart_df(df, horizon_days=horizon_days)


def _get_daily_demand_series(product_df: pd.DataFrame) -> pd.Series:
    return get_daily_demand_series(product_df)


def _calculate_expected_revenue(
    product_df: pd.DataFrame,
    predicted_quantity: float,
) -> float:
    if "selling_price" in product_df.columns:
        selling_price = pd.to_numeric(product_df["selling_price"], errors="coerce").dropna()
        if not selling_price.empty:
            return float(predicted_quantity * float(selling_price.iloc[-1]))

    total_revenue = float(pd.to_numeric(product_df["revenue"], errors="coerce").sum())
    total_quantity = float(pd.to_numeric(product_df["quantity_sold"], errors="coerce").sum())

    if total_quantity <= 0:
        return 0.0

    return float(predicted_quantity * (total_revenue / total_quantity))
