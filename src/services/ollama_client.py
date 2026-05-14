from __future__ import annotations

from dataclasses import dataclass
import os

import httpx


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str
    model: str
    timeout_seconds: int


class OllamaClientError(Exception):
    pass


def get_ollama_settings() -> OllamaSettings:
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).strip() or DEFAULT_OLLAMA_BASE_URL
    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL
    timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_OLLAMA_TIMEOUT_SECONDS)).strip()

    try:
        timeout_seconds = max(1, int(timeout_raw))
    except ValueError:
        timeout_seconds = DEFAULT_OLLAMA_TIMEOUT_SECONDS

    return OllamaSettings(
        base_url=base_url.rstrip("/"),
        model=model,
        timeout_seconds=timeout_seconds,
    )


class OllamaClient:
    def __init__(self, settings: OllamaSettings | None = None) -> None:
        self.settings = settings or get_ollama_settings()

    async def get_status(self) -> tuple[bool, str, str | None]:
        try:
            async with httpx.AsyncClient(timeout=min(self.settings.timeout_seconds, 10)) as client:
                response = await client.get(f"{self.settings.base_url}/api/tags")
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise OllamaClientError("timeout") from error
        except httpx.HTTPStatusError as error:
            raise OllamaClientError(f"http_{error.response.status_code}") from error
        except httpx.HTTPError as error:
            raise OllamaClientError("unavailable") from error

        data = response.json()
        models = data.get("models")
        if not isinstance(models, list):
            raise OllamaClientError("invalid_response")

        model_names = {
            str(item.get("name", "")).strip()
            for item in models
            if isinstance(item, dict)
        }
        if self.settings.model not in model_names:
            return (
                False,
                f"Модель {self.settings.model} не найдена в локальной Ollama.",
                "missing_model",
            )

        return (
            True,
            f"Ollama доступна, модель {self.settings.model} готова.",
            None,
        )

    async def generate(self, *, prompt: str, system_prompt: str) -> str:
        payload = {
            "model": self.settings.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
                response = await client.post(f"{self.settings.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise OllamaClientError("timeout") from error
        except httpx.HTTPStatusError as error:
            raise OllamaClientError(f"http_{error.response.status_code}") from error
        except httpx.HTTPError as error:
            raise OllamaClientError("unavailable") from error

        data = response.json()
        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaClientError("invalid_response")

        return answer.strip()
