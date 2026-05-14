from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """
    Конфигурация запуска аналитического ядра StockPilot AI.
    """

    input_file: Path
    output_file: Path
    dashboard_file: Path
    forecast_horizon_days: int = 14
    safety_stock_percent: float = 0.2
    supply_lead_time_days: int = 3


DEFAULT_CONFIG = AppConfig(
    input_file=Path("data/input/sample_sales.csv"),
    output_file=Path("data/output/stockpilot_report.xlsx"),
    dashboard_file=Path("data/output/dashboard.html"),
    forecast_horizon_days=14,
    safety_stock_percent=0.2,
    supply_lead_time_days=3,
)
