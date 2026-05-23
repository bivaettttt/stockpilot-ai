from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import CopilotStatusResponse, HealthResponse
from src.services.ai_provider import get_ai_provider

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="StockPilot AI API",
        version="0.2.0",
    )


@router.get("/ready", response_model=HealthResponse)
def readiness_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="StockPilot AI API",
        version="0.2.0",
    )


@router.get("/system/ai-status", response_model=CopilotStatusResponse)
async def ai_status() -> CopilotStatusResponse:
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
