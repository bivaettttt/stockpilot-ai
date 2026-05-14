import argparse
from pathlib import Path

from src.config import DEFAULT_CONFIG, AppConfig
from src.logger import setup_logger
from src.pipeline import DataValidationError, run_stockpilot_pipeline

logger = setup_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="StockPilot AI — локальное аналитическое ядро",
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_CONFIG.input_file),
        help="Путь к CSV/XLSX-файлу с продажами и остатками.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_CONFIG.output_file),
        help="Путь для сохранения Excel-отчёта.",
    )

    parser.add_argument(
        "--dashboard",
        type=str,
        default=str(DEFAULT_CONFIG.dashboard_file),
        help="Путь для сохранения HTML-дашборда.",
    )

    parser.add_argument(
        "--horizon",
        type=int,
        default=DEFAULT_CONFIG.forecast_horizon_days,
        help="Горизонт прогноза в днях.",
    )

    parser.add_argument(
        "--safety-stock",
        type=float,
        default=DEFAULT_CONFIG.safety_stock_percent,
        help="Процент страхового запаса. Например: 0.2 = 20%%.",
    )

    parser.add_argument(
        "--lead-time",
        type=int,
        default=DEFAULT_CONFIG.supply_lead_time_days,
        help="Срок поставки в днях.",
    )

    return parser.parse_args()


def build_config_from_args(args: argparse.Namespace) -> AppConfig:
    return AppConfig(
        input_file=Path(args.input),
        output_file=Path(args.output),
        dashboard_file=Path(args.dashboard),
        forecast_horizon_days=args.horizon,
        safety_stock_percent=args.safety_stock,
        supply_lead_time_days=args.lead_time,
    )


def print_start_message(config: AppConfig) -> None:
    print("StockPilot AI — локальное аналитическое ядро")
    print("=" * 60)
    print(f"Входной файл: {config.input_file}")
    print(f"Excel-отчёт: {config.output_file}")
    print(f"HTML-дашборд: {config.dashboard_file}")
    print(f"Горизонт прогноза: {config.forecast_horizon_days} дн.")
    print(f"Страховой запас: {int(config.safety_stock_percent * 100)}%")
    print(f"Срок поставки: {config.supply_lead_time_days} дн.")
    print("=" * 60)
    print()


def print_analysis_result(config: AppConfig, result) -> None:
    print("Анализ выполнен успешно.")
    print()

    print("Сводные показатели:")
    print("-" * 60)
    for key, value in result.summary_metrics.items():
        print(f"{key}: {value}")

    print()
    print("Управленческие выводы:")
    print("-" * 60)
    for insight in result.insights:
        print(f"- {insight}")

    print()
    print("Рекомендации по закупкам:")
    print("-" * 60)

    if result.recommendations.empty:
        print("Нет рекомендаций.")
    else:
        visible_columns = [
            "sku",
            "product_name",
            "priority",
            "recommended_order_qty",
            "message",
        ]

        print(result.recommendations[visible_columns])

    print()
    print("Excel-отчёт создан:")
    print(result.report_path)

    print()
    print("HTML-дашборд создан:")
    print(result.dashboard_path)

    print()
    print("Открыть дашборд в браузере:")
    print(f"open {result.dashboard_path}")

    print()
    print("Параметры анализа:")
    print(f"- горизонт прогноза: {config.forecast_horizon_days} дн.")
    print(f"- страховой запас: {int(config.safety_stock_percent * 100)}%")
    print(f"- срок поставки: {config.supply_lead_time_days} дн.")


def main() -> None:
    args = parse_args()
    config = build_config_from_args(args)

    print_start_message(config)

    try:
        result = run_stockpilot_pipeline(config)
        print_analysis_result(config, result)

    except DataValidationError as error:
        print("Данные не прошли проверку.")
        print()

        for validation_error in error.errors:
            print(f"- {validation_error}")

        print()
        print("Технические детали записаны в logs/stockpilot.log")

    except Exception as error:
        logger.exception("Analysis failed")

        print("Ошибка выполнения программы:")
        print(error)
        print()
        print("Технические детали записаны в logs/stockpilot.log")


if __name__ == "__main__":
    main()
