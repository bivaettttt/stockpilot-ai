from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.constants import HISTORY_DB_FILE, HISTORY_JSON_FILE
from src.domain.models import HistoryQuery, PaginatedHistoryResult


class HistoryRepository:
    def __init__(self, db_path: Path = HISTORY_DB_FILE, legacy_json_path: Path = HISTORY_JSON_FILE) -> None:
        self.db_path = db_path
        self.legacy_json_path = legacy_json_path
        self._migration_completed = False

    def ensure_storage(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    horizon INTEGER NOT NULL,
                    safety_stock REAL NOT NULL,
                    lead_time INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'success',
                    file_hash TEXT,
                    recommendations_count INTEGER NOT NULL DEFAULT 0,
                    analysis_duration_ms INTEGER,
                    report_path TEXT NOT NULL,
                    dashboard_path TEXT NOT NULL,
                    recommendations_csv_path TEXT,
                    abc_xyz_matrix_csv_path TEXT,
                    report_url TEXT NOT NULL,
                    dashboard_url TEXT NOT NULL,
                    recommendations_csv_url TEXT,
                    abc_xyz_matrix_csv_url TEXT,
                    summary_metrics_json TEXT NOT NULL,
                    data_quality_json TEXT,
                    result_snapshot_json TEXT,
                    decisions_json TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at
                ON analysis_history (created_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_history_filename
                ON analysis_history (original_filename)
                """
            )
            self._ensure_column(connection, "analysis_history", "result_snapshot_json", "TEXT")
            self._ensure_column(connection, "analysis_history", "decisions_json", "TEXT")
            connection.commit()

        if not self._migration_completed:
            self._migration_completed = True
            self._migrate_legacy_json()

    def add_record(self, record: dict[str, Any]) -> None:
        self.ensure_storage()
        payload = self._serialize_record(record)
        self._insert_payload(payload)

    def _insert_payload(self, payload: dict[str, Any]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analysis_history (
                    id,
                    created_at,
                    original_filename,
                    horizon,
                    safety_stock,
                    lead_time,
                    status,
                    file_hash,
                    recommendations_count,
                    analysis_duration_ms,
                    report_path,
                    dashboard_path,
                    recommendations_csv_path,
                    abc_xyz_matrix_csv_path,
                    report_url,
                    dashboard_url,
                    recommendations_csv_url,
                    abc_xyz_matrix_csv_url,
                    summary_metrics_json,
                    data_quality_json,
                    result_snapshot_json,
                    decisions_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["created_at"],
                    payload["original_filename"],
                    payload["horizon"],
                    payload["safety_stock"],
                    payload["lead_time"],
                    payload["status"],
                    payload["file_hash"],
                    payload["recommendations_count"],
                    payload["analysis_duration_ms"],
                    payload["report_path"],
                    payload["dashboard_path"],
                    payload["recommendations_csv_path"],
                    payload["abc_xyz_matrix_csv_path"],
                    payload["report_url"],
                    payload["dashboard_url"],
                    payload["recommendations_csv_url"],
                    payload["abc_xyz_matrix_csv_url"],
                    json.dumps(payload["summary_metrics"], ensure_ascii=False),
                    json.dumps(payload["data_quality"], ensure_ascii=False)
                    if payload["data_quality"] is not None
                    else None,
                    json.dumps(payload["result_snapshot"], ensure_ascii=False)
                    if payload["result_snapshot"] is not None
                    else None,
                    json.dumps(payload["decisions"], ensure_ascii=False),
                ),
            )
            connection.commit()

    def list_records(self, query: HistoryQuery | None = None) -> PaginatedHistoryResult:
        self.ensure_storage()
        safe_query = query or HistoryQuery()

        where_clauses: list[str] = []
        parameters: list[Any] = []

        if safe_query.original_filename:
            where_clauses.append("original_filename LIKE ?")
            parameters.append(f"%{safe_query.original_filename}%")

        if safe_query.status:
            where_clauses.append("status = ?")
            parameters.append(safe_query.status)

        if safe_query.file_hash:
            where_clauses.append("file_hash = ?")
            parameters.append(safe_query.file_hash)

        if safe_query.date_from:
            where_clauses.append("created_at >= ?")
            parameters.append(safe_query.date_from)

        if safe_query.date_to:
            where_clauses.append("created_at <= ?")
            parameters.append(safe_query.date_to)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row

            total_records = int(
                connection.execute(
                    f"SELECT COUNT(*) AS total FROM analysis_history {where_sql}",
                    parameters,
                ).fetchone()["total"]
            )

            rows = connection.execute(
                f"""
                SELECT *
                FROM analysis_history
                {where_sql}
                ORDER BY datetime(created_at) DESC
                LIMIT ? OFFSET ?
                """,
                [*parameters, safe_query.page_size, safe_query.offset],
            ).fetchall()

        records = [self._deserialize_record(dict(row)) for row in rows]

        return PaginatedHistoryResult(
            records=records,
            total_records=total_records,
            page=safe_query.page,
            page_size=safe_query.page_size,
        )

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM analysis_history WHERE id = ? LIMIT 1",
                (record_id,),
            ).fetchone()

        if row is None:
            return None

        return self._deserialize_record(dict(row))

    def get_result_snapshot(self, record_id: str) -> dict[str, Any] | None:
        record = self.get_record(record_id)
        if record is None:
            return None
        snapshot = record.get("result_snapshot")
        return snapshot if isinstance(snapshot, dict) else None

    def get_decisions(self, record_id: str) -> dict[str, Any] | None:
        record = self.get_record(record_id)
        if record is None:
            return None
        decisions = record.get("decisions")
        return decisions if isinstance(decisions, dict) else {}

    def save_decisions(self, record_id: str, decisions: dict[str, Any]) -> bool:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                UPDATE analysis_history
                SET decisions_json = ?
                WHERE id = ?
                """,
                (json.dumps(decisions, ensure_ascii=False), record_id),
            )
            connection.commit()

        return cursor.rowcount > 0

    def _migrate_legacy_json(self) -> None:
        if not self.legacy_json_path.exists():
            return

        try:
            legacy_payload = json.loads(self.legacy_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        if not isinstance(legacy_payload, list) or not legacy_payload:
            return

        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM analysis_history"
            ).fetchone()
            if row[0] > 0:
                return

        for record in legacy_payload:
            if isinstance(record, dict):
                self._insert_payload(self._serialize_record(record))

    def _serialize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now().isoformat(timespec="seconds")
        return {
            "id": str(record.get("id")),
            "created_at": record.get("created_at", now),
            "original_filename": record.get("original_filename", "uploaded_file"),
            "horizon": int(record.get("horizon", 14)),
            "safety_stock": float(record.get("safety_stock", 0.2)),
            "lead_time": int(record.get("lead_time", 3)),
            "status": record.get("status", "success"),
            "file_hash": record.get("file_hash"),
            "recommendations_count": int(record.get("recommendations_count", 0)),
            "analysis_duration_ms": record.get("analysis_duration_ms"),
            "report_path": record.get("report_path", ""),
            "dashboard_path": record.get("dashboard_path", ""),
            "recommendations_csv_path": record.get("recommendations_csv_path"),
            "abc_xyz_matrix_csv_path": record.get("abc_xyz_matrix_csv_path"),
            "report_url": record.get("report_url", ""),
            "dashboard_url": record.get("dashboard_url", ""),
            "recommendations_csv_url": record.get("recommendations_csv_url"),
            "abc_xyz_matrix_csv_url": record.get("abc_xyz_matrix_csv_url"),
            "summary_metrics": record.get("summary_metrics", {}),
            "data_quality": record.get("data_quality"),
            "result_snapshot": record.get("result_snapshot"),
            "decisions": record.get("decisions", {}),
        }

    def _deserialize_record(self, row: dict[str, Any]) -> dict[str, Any]:
        row["summary_metrics"] = _safe_json_loads(row.get("summary_metrics_json"), {})
        row["data_quality"] = _safe_json_loads(row.get("data_quality_json"), None)
        row["result_snapshot"] = _safe_json_loads(row.get("result_snapshot_json"), None)
        row["decisions"] = _safe_json_loads(row.get("decisions_json"), {})
        row["has_result_snapshot"] = row["result_snapshot"] is not None
        row["has_saved_decisions"] = bool(row["decisions"])
        row.pop("summary_metrics_json", None)
        row.pop("data_quality_json", None)
        row.pop("result_snapshot_json", None)
        row.pop("decisions_json", None)
        return row

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_definition: str,
    ) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in existing_columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )


def build_history_record(
    request_id: str,
    original_filename: str,
    horizon: int,
    safety_stock: float,
    lead_time: int,
    summary_metrics: dict[str, Any],
    recommendations_count: int,
    report_path: str,
    dashboard_path: str,
    report_url: str,
    dashboard_url: str,
    recommendations_csv_path: str,
    recommendations_csv_url: str,
    abc_xyz_matrix_csv_path: str,
    abc_xyz_matrix_csv_url: str,
    status: str = "success",
    file_hash: str | None = None,
    data_quality: dict[str, Any] | None = None,
    analysis_duration_ms: int | None = None,
) -> dict[str, Any]:
    return {
        "id": request_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "original_filename": original_filename,
        "horizon": horizon,
        "safety_stock": safety_stock,
        "lead_time": lead_time,
        "status": status,
        "file_hash": file_hash,
        "summary_metrics": summary_metrics,
        "recommendations_count": recommendations_count,
        "analysis_duration_ms": analysis_duration_ms,
        "report_path": report_path,
        "dashboard_path": dashboard_path,
        "report_url": report_url,
        "dashboard_url": dashboard_url,
        "recommendations_csv_path": recommendations_csv_path,
        "recommendations_csv_url": recommendations_csv_url,
        "abc_xyz_matrix_csv_path": abc_xyz_matrix_csv_path,
        "abc_xyz_matrix_csv_url": abc_xyz_matrix_csv_url,
        "data_quality": data_quality,
    }


def _safe_json_loads(raw: Any, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback
