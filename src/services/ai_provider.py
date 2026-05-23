from __future__ import annotations

from dataclasses import dataclass

from src.config import get_ai_config
from src.services.yandex_gpt_client import YandexGPTClient, YandexGPTClientError


NOT_CONFIGURED_MESSAGE = "AI-помощник не настроен. Добавьте YANDEX_GPT_API_KEY и YANDEX_GPT_FOLDER_ID в .env."


@dataclass(frozen=True)
class AIProviderStatus:
    provider: str
    configured: bool
    available: bool
    model: str
    message: str
    uses_external_ai: bool = True
    error_code: str | None = None


class AIProvider:
    provider = "yandex"
    uses_external_ai = True

    def __init__(self) -> None:
        self.client = YandexGPTClient(get_ai_config())

    @property
    def model(self) -> str:
        return self.client.config.yandex_gpt_model

    @property
    def model_uri(self) -> str:
        return self.client.model_uri

    def is_configured(self) -> bool:
        return self.client.is_configured()

    async def status(self) -> AIProviderStatus:
        status = await self.client.healthcheck()
        message = status.message
        if not status.configured:
            message = NOT_CONFIGURED_MESSAGE
        return AIProviderStatus(
            provider=self.provider,
            configured=status.configured,
            available=status.available,
            model=status.model,
            message=message,
            uses_external_ai=self.uses_external_ai,
            error_code=status.error_code,
        )

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        try:
            return await self.client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        except YandexGPTClientError:
            raise


def get_ai_provider() -> AIProvider:
    return AIProvider()
