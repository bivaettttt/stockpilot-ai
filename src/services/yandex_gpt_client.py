from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.config import AIConfig, get_ai_config


class YandexGPTClientError(Exception):
    pass


@dataclass(frozen=True)
class YandexGPTStatus:
    configured: bool
    available: bool
    model: str
    message: str
    error_code: str | None = None


class YandexGPTClient:
    def __init__(self, config: AIConfig | None = None) -> None:
        self.config = config or get_ai_config()

    @property
    def model_uri(self) -> str:
        model = self.config.yandex_gpt_model.strip()
        if model.startswith("gpt://"):
            return model
        folder_id = self.config.yandex_gpt_folder_id or ""
        return f"gpt://{folder_id}/{model}"

    def is_configured(self) -> bool:
        has_model_uri = self.config.yandex_gpt_model.strip().startswith("gpt://")
        return bool(self.config.yandex_gpt_api_key and (self.config.yandex_gpt_folder_id or has_model_uri))

    async def healthcheck(self) -> YandexGPTStatus:
        if not self.is_configured():
            return YandexGPTStatus(
                configured=False,
                available=False,
                model=self.config.yandex_gpt_model,
                message="YandexGPT API key or folder id is not configured",
                error_code="not_configured",
            )

        try:
            await self.complete(
                system_prompt="Ты проверяешь доступность AI-провайдера. Ответь одним словом: ok.",
                user_prompt="healthcheck",
                max_tokens=8,
            )
        except YandexGPTClientError as error:
            return YandexGPTStatus(
                configured=True,
                available=False,
                model=self.config.yandex_gpt_model,
                message=_safe_error_message(str(error)),
                error_code=str(error),
            )

        return YandexGPTStatus(
            configured=True,
            available=True,
            model=self.config.yandex_gpt_model,
            message="YandexGPT подключён.",
        )

    async def complete(self, *, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> str:
        if not self.is_configured():
            raise YandexGPTClientError("not_configured")

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": self.config.yandex_gpt_temperature,
                "maxTokens": str(max_tokens or self.config.yandex_gpt_max_tokens),
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Api-Key {self.config.yandex_gpt_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.yandex_gpt_timeout_seconds) as client:
                response = await client.post(self.config.yandex_gpt_base_url, json=payload, headers=headers)
        except httpx.TimeoutException as error:
            raise YandexGPTClientError("timeout") from error
        except httpx.HTTPError as error:
            raise YandexGPTClientError("provider_unavailable") from error

        if response.status_code != 200:
            raise YandexGPTClientError(f"http_{response.status_code}")

        try:
            data = response.json()
        except ValueError as error:
            raise YandexGPTClientError("invalid_response") from error

        answer = _extract_answer(data)
        if not answer:
            raise YandexGPTClientError("invalid_response")
        return answer


def _extract_answer(data: dict[str, Any]) -> str | None:
    alternatives = data.get("result", {}).get("alternatives")
    if not isinstance(alternatives, list) or not alternatives:
        return None
    first = alternatives[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    text = message.get("text")
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    return stripped or None


def _safe_error_message(error_code: str) -> str:
    if error_code == "not_configured":
        return "YandexGPT API key or folder id is not configured"
    if error_code == "timeout":
        return "YandexGPT request timed out"
    if error_code.startswith("http_"):
        return f"YandexGPT returned {error_code}"
    return "YandexGPT is unavailable"
