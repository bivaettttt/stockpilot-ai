from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import HealthResponse

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

