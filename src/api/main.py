from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from src.api.history import ensure_history_file
from src.api.procurement import ensure_procurement_storage
from src.api.routers import (
    analysis_router,
    copilot_router,
    files_router,
    history_router,
    import_router,
    procurement_router,
    settings_router,
    system_router,
)
from src.api.templates import ensure_template_file
from src.api.utils import ensure_api_dirs
from src.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ensure_api_dirs()
    ensure_template_file()
    ensure_history_file()
    ensure_procurement_storage()
    logger.info("StockPilot AI API started")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="StockPilot AI API",
        description="API для анализа продаж, прогнозирования спроса и рекомендаций по закупкам.",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid4().hex[:8])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    for router in [
        system_router,
        history_router,
        import_router,
        procurement_router,
        analysis_router,
        files_router,
        settings_router,
        copilot_router,
    ]:
        app.include_router(router)
        app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
