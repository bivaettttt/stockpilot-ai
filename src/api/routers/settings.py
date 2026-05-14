from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.api.schemas import WorkspaceSettingsResponse
from src.domain.constants import API_OUTPUT_DIR

router = APIRouter(tags=["Settings"])

SETTINGS_FILE = API_OUTPUT_DIR / "workspace_settings.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "locale": "ru",
    "theme": "system",
    "density": "comfortable",
    "workspaceName": "StockPilot Workspace",
}


def _read_settings() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_SETTINGS


def _write_settings(data: dict[str, Any]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@router.get("/settings", response_model=WorkspaceSettingsResponse)
def get_settings() -> WorkspaceSettingsResponse:
    return WorkspaceSettingsResponse(status="success", data=_read_settings())


@router.put("/settings", response_model=WorkspaceSettingsResponse)
def update_settings(payload: dict[str, Any]) -> WorkspaceSettingsResponse:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid settings payload")
    next_settings = {**DEFAULT_SETTINGS, **_read_settings(), **payload}
    _write_settings(next_settings)
    return WorkspaceSettingsResponse(status="success", data=next_settings)
