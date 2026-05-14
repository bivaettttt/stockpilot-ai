from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.history import (
    read_history_decisions,
    read_history_paginated,
    read_history_record,
    read_history_result,
    save_history_decisions,
)
from src.api.schemas import (
    AnalyzeResponse,
    HistoryDecisionsResponse,
    HistoryFilesResponse,
    HistoryArtifactFile,
    HistoryRecord,
    HistoryResponse,
    PaginationResponse,
)

router = APIRouter(tags=["History"])


@router.get("/history", response_model=HistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    original_filename: str | None = Query(None),
    status: str | None = Query(None),
    file_hash: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> HistoryResponse:
    result = read_history_paginated(
        page=page,
        page_size=page_size,
        original_filename=original_filename,
        status=status,
        file_hash=file_hash,
        date_from=date_from,
        date_to=date_to,
    )

    return HistoryResponse(
        status="success",
        records=result.records,
        pagination=PaginationResponse(
            page=result.page,
            page_size=result.page_size,
            total_records=result.total_records,
            total_pages=result.total_pages,
        ),
    )


@router.get("/history/{run_id}", response_model=HistoryRecord)
def get_history_detail(run_id: str) -> HistoryRecord:
    record = read_history_record(run_id)
    if record is None:
        raise _not_found()
    return HistoryRecord(**record)


@router.get("/history/{run_id}/result", response_model=AnalyzeResponse)
def get_history_result(run_id: str) -> AnalyzeResponse:
    snapshot = read_history_result(run_id)
    if snapshot is None:
        record = read_history_record(run_id)
        if record is None:
            raise _not_found()
        raise HTTPException(
            status_code=404,
            detail={"message": "Для этого анализа не найден сохранённый результат."},
        )
    return AnalyzeResponse(**snapshot)


@router.get("/history/{run_id}/files", response_model=HistoryFilesResponse)
def get_history_files(run_id: str) -> HistoryFilesResponse:
    record = read_history_record(run_id)
    if record is None:
        raise _not_found()

    return HistoryFilesResponse(
        run_id=run_id,
        files=[
            _build_artifact("report", "Excel-отчёт", record.get("report_path"), record.get("report_url")),
            _build_artifact("dashboard", "HTML dashboard", record.get("dashboard_path"), record.get("dashboard_url")),
            _build_artifact(
                "recommendations_csv",
                "CSV рекомендаций",
                record.get("recommendations_csv_path"),
                record.get("recommendations_csv_url"),
            ),
            _build_artifact(
                "abc_xyz_csv",
                "Матрица ABC/XYZ",
                record.get("abc_xyz_matrix_csv_path"),
                record.get("abc_xyz_matrix_csv_url"),
            ),
        ],
    )


@router.get("/history/{run_id}/decisions", response_model=HistoryDecisionsResponse)
def get_history_decisions(run_id: str) -> HistoryDecisionsResponse:
    decisions = read_history_decisions(run_id)
    if decisions is None:
        raise _not_found()
    return HistoryDecisionsResponse(run_id=run_id, decisions=decisions)


@router.put("/history/{run_id}/decisions", response_model=HistoryDecisionsResponse)
def put_history_decisions(run_id: str, payload: dict[str, Any]) -> HistoryDecisionsResponse:
    if not save_history_decisions(run_id, payload):
        raise _not_found()
    return HistoryDecisionsResponse(run_id=run_id, decisions=payload)


def _build_artifact(kind: str, title: str, path: str | None, url: str | None) -> HistoryArtifactFile:
    available = bool(path and Path(path).exists())
    return HistoryArtifactFile(
        kind=kind,
        title=title,
        path=path,
        url=url,
        available=available,
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"message": "Анализ с таким run_id не найден."})
