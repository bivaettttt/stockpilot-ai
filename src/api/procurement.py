from __future__ import annotations

from typing import Any

from src.repositories.procurement_repository import ProcurementRepository

repository = ProcurementRepository()


def ensure_procurement_storage() -> None:
    repository.ensure_storage()


def list_suppliers() -> list[dict[str, Any]]:
    return repository.list_suppliers()


def get_supplier(supplier_id: str) -> dict[str, Any] | None:
    return repository.get_supplier(supplier_id)


def save_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    return repository.upsert_supplier(payload)


def remove_supplier(supplier_id: str) -> bool:
    return repository.delete_supplier(supplier_id)


def list_sku_settings() -> list[dict[str, Any]]:
    return repository.list_sku_settings()


def get_sku_setting(sku: str) -> dict[str, Any] | None:
    return repository.get_sku_setting(sku)


def save_sku_setting(payload: dict[str, Any]) -> dict[str, Any]:
    return repository.upsert_sku_setting(payload)


def remove_sku_setting(sku: str) -> bool:
    return repository.delete_sku_setting(sku)
