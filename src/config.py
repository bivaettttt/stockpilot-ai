from dataclasses import dataclass
import os
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


YANDEX_GPT_DEFAULT_BASE_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


@dataclass(frozen=True)
class AIConfig:
    ai_provider: str = "yandex"
    yandex_gpt_api_key: str | None = None
    yandex_gpt_folder_id: str | None = None
    yandex_gpt_model: str = "yandexgpt-5-lite"
    yandex_gpt_base_url: str = YANDEX_GPT_DEFAULT_BASE_URL
    yandex_gpt_timeout_seconds: int = 30
    yandex_gpt_temperature: float = 0.2
    yandex_gpt_max_tokens: int = 1200


def get_ai_config() -> AIConfig:
    return AIConfig(
        ai_provider=_env_str("AI_PROVIDER", "yandex").lower(),
        yandex_gpt_api_key=_env_optional("YANDEX_GPT_API_KEY"),
        yandex_gpt_folder_id=_env_optional("YANDEX_GPT_FOLDER_ID"),
        yandex_gpt_model=_env_str("YANDEX_GPT_MODEL", "yandexgpt-5-lite"),
        yandex_gpt_base_url=_env_str("YANDEX_GPT_BASE_URL", YANDEX_GPT_DEFAULT_BASE_URL),
        yandex_gpt_timeout_seconds=_env_int("YANDEX_GPT_TIMEOUT_SECONDS", 30, minimum=1),
        yandex_gpt_temperature=_env_float("YANDEX_GPT_TEMPERATURE", 0.2, minimum=0.0, maximum=1.0),
        yandex_gpt_max_tokens=_env_int("YANDEX_GPT_MAX_TOKENS", 1200, minimum=1),
    )


def _env_str(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_int(name: str, default: int, *, minimum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default
    return max(minimum, value)


def _env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)).strip())
    except ValueError:
        return default
    return min(maximum, max(minimum, value))
