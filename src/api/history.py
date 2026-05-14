from __future__ import annotations

from typing import Any

from src.domain.constants import DEFAULT_HISTORY_PAGE_SIZE, MAX_HISTORY_PAGE_SIZE
from src.domain.models import HistoryQuery, PaginatedHistoryResult
from src.repositories.history_repository import (
    HistoryRepository,
    build_history_record,
)

repository = HistoryRepository()


def ensure_history_file() -> None:
    repository.ensure_storage()


def read_history() -> list[dict[str, Any]]:
    result = repository.list_records(
        HistoryQuery(page=1, page_size=50)
    )
    return result.records


def read_history_paginated(
    page: int = 1,
    page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
    original_filename: str | None = None,
    status: str | None = None,
    file_hash: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> PaginatedHistoryResult:
    normalized_page_size = min(max(page_size, 1), MAX_HISTORY_PAGE_SIZE)
    query = HistoryQuery(
        page=max(page, 1),
        page_size=normalized_page_size,
        original_filename=original_filename,
        status=status,
        file_hash=file_hash,
        date_from=date_from,
        date_to=date_to,
    )
    return repository.list_records(query)


def add_history_record(record: dict[str, Any]) -> None:
    repository.add_record(record)


def read_history_record(record_id: str) -> dict[str, Any] | None:
    return repository.get_record(record_id)


def read_history_result(record_id: str) -> dict[str, Any] | None:
    return repository.get_result_snapshot(record_id)


def read_history_decisions(record_id: str) -> dict[str, Any] | None:
    return repository.get_decisions(record_id)


def save_history_decisions(record_id: str, decisions: dict[str, Any]) -> bool:
    return repository.save_decisions(record_id, decisions)


__all__ = [
    "add_history_record",
    "build_history_record",
    "ensure_history_file",
    "read_history",
    "read_history_decisions",
    "read_history_paginated",
    "read_history_record",
    "read_history_result",
    "save_history_decisions",
]
