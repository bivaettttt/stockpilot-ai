from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.schemas import (
    CopilotStatusResponse,
    CopilotStreamRequest,
    ImportAssistRequest,
    ImportAssistResponse,
)
from src.logger import setup_logger
from src.services.ai_provider import NOT_CONFIGURED_MESSAGE, get_ai_provider
from src.services.copilot_context import build_analysis_assist_context, build_import_assist_context
from src.services.yandex_gpt_client import YandexGPTClientError

router = APIRouter(tags=["Copilot"])
logger = setup_logger()


def _build_answer(payload: CopilotStreamRequest) -> str:
    kpis = payload.context.get("kpis", {})
    urgent = kpis.get("urgentCount")
    overstock = kpis.get("overstockCount")
    confidence = kpis.get("confidence")
    selected = payload.selected_sku or "n/a"
    page = payload.active_page or "overview"

    lines = [
        f"### Ответ Copilot ({datetime.now(timezone.utc).strftime('%H:%M:%S UTC')})",
        "",
        f"Вопрос: {payload.message}",
        "",
        f"- Активная страница: **{page}**",
        f"- Выбранный SKU: **{selected}**",
        f"- Срочные позиции: **{urgent if urgent is not None else '-'}**",
        f"- Избыточные остатки: **{overstock if overstock is not None else '-'}**",
        f"- Медианная надёжность: **{confidence if confidence is not None else '-'}**",
        "",
        "Следующие действия:",
        "1. Проверьте SKU с самым высоким риском в закупочном плане.",
        "2. Сравните надёжность прогноза на странице прогноза.",
        "3. Экспортируйте список действий для закупочной проверки.",
    ]
    return "\n".join(lines)


@router.post("/copilot/stream")
async def copilot_stream(payload: CopilotStreamRequest) -> StreamingResponse:
    answer = _build_answer(payload)
    chunks = answer.split(" ")

    async def event_generator():
        for token in chunks:
            data = {"type": "token", "value": f"{token} "}
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def build_import_assist_system_prompt() -> str:
    return (
        "Ты Copilot StockPilot AI.\n"
        "Ты помогаешь пользователю подготовить CSV/XLSX файл для анализа продаж и остатков.\n"
        "Отвечай только по переданному агрегированному контексту анализа.\n"
        "Ты не выдумываешь колонки, значения, метрики или выводы.\n"
        "Если данных нет, скажи, что в текущем анализе этого нет.\n"
        "Ты не меняешь файл и не подтверждаешь mapping за пользователя.\n"
        "Пиши по-русски, коротко, управленчески, с конкретными действиями.\n"
        "Не обещай точность прогноза.\n"
        "Не упоминай OpenAI.\n"
        "Не отправляй пользователя к внешним AI-сервисам."
    )


def build_analysis_assist_system_prompt() -> str:
    return (
        "Ты Copilot StockPilot AI.\n"
        "Ты помогаешь объяснять анализ продаж, запасов, прогнозов и закупочных рекомендаций.\n"
        "Отвечай только по переданному агрегированному контексту анализа.\n"
        "Не выдумывай SKU, цифры, метрики, поставщиков, прогнозы или рекомендации.\n"
        "Если данных нет, скажи, что в текущем анализе этого нет.\n"
        "Не обещай точность прогноза и не используй слово 'точность' как гарантию результата.\n"
        "Не используй формулировки вроде 'гарантированно', 'точно', '97% accuracy'.\n"
        "Трактуй confidence аккуратно: high — высокая надёжность, medium — средняя надёжность, "
        "low — низкая надёжность, insufficient_data — данных недостаточно.\n"
        "Если confidence medium, не называй это низкой точностью: скажи, что рекомендации можно использовать, "
        "но ключевые SKU стоит проверить вручную.\n"
        "Если forecast confidence низкий, обязательно упомяни это: низкая надёжность означает необходимость ручной проверки.\n"
        "Если есть warnings по stockout, promo или insufficient history, учитывай их в ответе.\n"
        "Не меняй закупочный план сам.\n"
        "Не подтверждай решения за пользователя.\n"
        "Пиши по-русски, коротко, управленчески, с конкретными действиями.\n"
        "Не упоминай OpenAI.\n"
        "Не отправляй пользователя к внешним AI-сервисам."
    )


def build_import_assist_prompt(*, question: str, context: dict[str, object]) -> str:
    return (
        "Вопрос пользователя:\n"
        f"{question.strip()}\n\n"
        "Контекст по файлу:\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Ответь по-русски. Если файл не готов к анализу, явно скажи почему и что исправить."
    )


async def generate_import_assist_answer(question: str, context: dict[str, object]) -> tuple[str, str]:
    provider = get_ai_provider()
    answer = await provider.complete(
        user_prompt=build_import_assist_prompt(question=question, context=context),
        system_prompt=build_import_assist_system_prompt(),
    )
    return answer, provider.model


def build_analysis_assist_prompt(*, question: str, context: dict[str, object]) -> str:
    return (
        "Вопрос пользователя:\n"
        f"{question.strip()}\n\n"
        "Контекст анализа:\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Ответь по-русски. Объясняй только то, что видно в контексте. Если данных недостаточно, скажи об этом прямо."
    )


async def generate_analysis_assist_answer(question: str, context: dict[str, object]) -> tuple[str, str]:
    provider = get_ai_provider()
    answer = await provider.complete(
        user_prompt=build_analysis_assist_prompt(question=question, context=context),
        system_prompt=build_analysis_assist_system_prompt(),
    )
    return answer, provider.model


def _message_for_provider_error(error_code: str | None) -> str:
    if error_code == "not_configured":
        return NOT_CONFIGURED_MESSAGE
    if error_code == "timeout":
        return "AI-помощник не ответил вовремя. Проверьте доступ к YandexGPT и повторите запрос."
    if error_code and error_code.startswith("http_"):
        return "AI-помощник сейчас недоступен: YandexGPT вернул ошибку. Проверьте настройки ключа и каталога."
    return "AI-помощник сейчас недоступен. Проверьте настройки YandexGPT в .env."


def _fallback_import_assist_response(
    message: str | None = None,
    *,
    error_code: str | None = None,
) -> ImportAssistResponse:
    provider = get_ai_provider()
    return ImportAssistResponse(
        answer=message or _message_for_provider_error(error_code),
        model=provider.model,
        provider=provider.provider,
        is_local=False,
        fallback=True,
        error_code=error_code,
    )


def _fallback_analysis_assist_response(
    message: str | None = None,
    *,
    error_code: str | None = None,
) -> ImportAssistResponse:
    provider = get_ai_provider()
    return ImportAssistResponse(
        answer=message or _message_for_provider_error(error_code),
        model=provider.model,
        provider=provider.provider,
        is_local=False,
        fallback=True,
        error_code=error_code,
    )


@router.get("/copilot/status", response_model=CopilotStatusResponse)
async def copilot_status() -> CopilotStatusResponse:
    try:
        provider = get_ai_provider()
        status = await provider.status()
        return CopilotStatusResponse(
            provider=status.provider,
            is_local=False,
            uses_external_ai=status.uses_external_ai,
            configured=status.configured,
            model=status.model,
            available=status.available,
            message=status.message,
            error_code=status.error_code,
        )
    except Exception:
        logger.exception("Copilot status failed unexpectedly")
        provider = get_ai_provider()
        return CopilotStatusResponse(
            provider=provider.provider,
            is_local=False,
            uses_external_ai=True,
            configured=provider.is_configured(),
            model=provider.model,
            available=False,
            message=_message_for_provider_error("provider_unavailable"),
            error_code="provider_unavailable",
        )


@router.post("/copilot/import-assist", response_model=ImportAssistResponse)
async def copilot_import_assist(payload: ImportAssistRequest) -> ImportAssistResponse:
    compact_context = build_import_assist_context(payload.context)

    try:
        answer, model = await generate_import_assist_answer(payload.question, compact_context)
        return ImportAssistResponse(
            answer=answer,
            model=model,
            provider="yandex",
            is_local=False,
            fallback=False,
        )
    except YandexGPTClientError as error:
        logger.warning("Import assist unavailable: %s", error)
        return _fallback_import_assist_response(error_code=str(error))
    except Exception:
        logger.exception("Import assist failed unexpectedly")
        return _fallback_import_assist_response(error_code="unavailable")


@router.post("/copilot/analysis-assist", response_model=ImportAssistResponse)
async def copilot_analysis_assist(payload: ImportAssistRequest) -> ImportAssistResponse:
    compact_context = build_analysis_assist_context(payload.context)

    try:
        answer, model = await generate_analysis_assist_answer(payload.question, compact_context)
        return ImportAssistResponse(
            answer=answer,
            model=model,
            provider="yandex",
            is_local=False,
            fallback=False,
        )
    except YandexGPTClientError as error:
        logger.warning("Analysis assist unavailable: %s", error)
        return _fallback_analysis_assist_response(error_code=str(error))
    except Exception:
        logger.exception("Analysis assist failed unexpectedly")
        return _fallback_analysis_assist_response(error_code="unavailable")
