from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.constants import HISTORY_DB_FILE


class ProcurementRepository:
    def __init__(self, db_path: Path = HISTORY_DB_FILE) -> None:
        self.db_path = db_path

    def ensure_storage(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS suppliers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact_name TEXT,
                    email TEXT,
                    phone TEXT,
                    default_lead_time_days INTEGER NOT NULL DEFAULT 0,
                    min_order_value REAL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sku_settings (
                    sku TEXT PRIMARY KEY,
                    product_name TEXT,
                    supplier_id TEXT,
                    purchase_price REAL,
                    selling_price REAL,
                    lead_time_days INTEGER,
                    moq INTEGER,
                    pack_size INTEGER,
                    safety_stock_override REAL,
                    notes TEXT,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers (name)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sku_settings_supplier_id ON sku_settings (supplier_id)"
            )
            connection.commit()

    def list_suppliers(self) -> list[dict[str, Any]]:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM suppliers ORDER BY lower(name) ASC, datetime(updated_at) DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_supplier(self, supplier_id: str) -> dict[str, Any] | None:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM suppliers WHERE id = ? LIMIT 1",
                (supplier_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_supplier(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure_storage()
        now = datetime.now().isoformat(timespec="seconds")
        created_at = payload.get("created_at", now)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO suppliers (
                    id, name, contact_name, email, phone, default_lead_time_days,
                    min_order_value, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["id"],
                    payload["name"],
                    payload.get("contact_name"),
                    payload.get("email"),
                    payload.get("phone"),
                    payload.get("default_lead_time_days", 0),
                    payload.get("min_order_value"),
                    payload.get("notes"),
                    created_at,
                    now,
                ),
            )
            connection.commit()
        record = self.get_supplier(str(payload["id"]))
        if record is None:
            raise RuntimeError("Supplier was not persisted.")
        return record

    def delete_supplier(self, supplier_id: str) -> bool:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE sku_settings SET supplier_id = NULL WHERE supplier_id = ?",
                (supplier_id,),
            )
            cursor = connection.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            connection.commit()
        return cursor.rowcount > 0

    def list_sku_settings(self) -> list[dict[str, Any]]:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT
                    sku_settings.*,
                    suppliers.name AS supplier_name,
                    suppliers.default_lead_time_days AS supplier_default_lead_time_days
                FROM sku_settings
                LEFT JOIN suppliers ON suppliers.id = sku_settings.supplier_id
                ORDER BY lower(sku_settings.sku) ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_sku_setting(self, sku: str) -> dict[str, Any] | None:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT
                    sku_settings.*,
                    suppliers.name AS supplier_name,
                    suppliers.default_lead_time_days AS supplier_default_lead_time_days
                FROM sku_settings
                LEFT JOIN suppliers ON suppliers.id = sku_settings.supplier_id
                WHERE sku_settings.sku = ?
                LIMIT 1
                """,
                (sku,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_sku_setting(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure_storage()
        now = datetime.now().isoformat(timespec="seconds")
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO sku_settings (
                    sku, product_name, supplier_id, purchase_price, selling_price,
                    lead_time_days, moq, pack_size, safety_stock_override, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["sku"],
                    payload.get("product_name"),
                    payload.get("supplier_id"),
                    payload.get("purchase_price"),
                    payload.get("selling_price"),
                    payload.get("lead_time_days"),
                    payload.get("moq"),
                    payload.get("pack_size"),
                    payload.get("safety_stock_override"),
                    payload.get("notes"),
                    now,
                ),
            )
            connection.commit()
        record = self.get_sku_setting(str(payload["sku"]))
        if record is None:
            raise RuntimeError("SKU setting was not persisted.")
        return record

    def delete_sku_setting(self, sku: str) -> bool:
        self.ensure_storage()
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute("DELETE FROM sku_settings WHERE sku = ?", (sku,))
            connection.commit()
        return cursor.rowcount > 0
