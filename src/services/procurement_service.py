from __future__ import annotations

from math import ceil
from typing import Any


def enrich_procurement_plan(
    items: list[dict[str, Any]],
    suppliers: list[dict[str, Any]],
    sku_settings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    suppliers_by_id = {str(item["id"]): item for item in suppliers}
    sku_settings_by_sku = {str(item["sku"]): item for item in sku_settings}

    enriched_items: list[dict[str, Any]] = []
    for item in items:
        sku = str(item.get("sku", "")).strip()
        settings = sku_settings_by_sku.get(sku, {})
        supplier_record = suppliers_by_id.get(str(settings.get("supplier_id") or ""), None)

        supplier_name, supplier_source = _resolve_value(
            file_value=item.get("supplier"),
            settings_value=supplier_record.get("name") if supplier_record else None,
        )
        purchase_price, purchase_price_source = _resolve_numeric_value(
            file_value=item.get("purchase_price"),
            settings_value=settings.get("purchase_price"),
        )
        selling_price, selling_price_source = _resolve_numeric_value(
            file_value=item.get("selling_price"),
            settings_value=settings.get("selling_price"),
        )
        lead_time_days, lead_time_source = _resolve_numeric_value(
            file_value=None,
            settings_value=settings.get("lead_time_days") if settings.get("lead_time_days") is not None else (supplier_record.get("default_lead_time_days") if supplier_record else None),
        )
        moq, moq_source = _resolve_numeric_value(
            file_value=None,
            settings_value=settings.get("moq"),
        )
        pack_size, pack_size_source = _resolve_numeric_value(
            file_value=None,
            settings_value=settings.get("pack_size"),
        )

        system_qty = max(0, int(round(float(item.get("recommended_order_qty") or 0))))
        adjusted_qty, adjustment_reason = _apply_constraints(
            recommended_order_qty=system_qty,
            moq=int(moq) if moq is not None else None,
            pack_size=int(pack_size) if pack_size is not None else None,
        )
        estimated_cost = adjusted_qty * purchase_price if purchase_price is not None else None

        enriched_items.append(
            {
                **item,
                "system_recommended_qty": system_qty,
                "adjusted_order_qty": adjusted_qty,
                "adjustment_reason": adjustment_reason,
                "supplier_name": supplier_name,
                "supplier_lead_time_days": int(lead_time_days) if lead_time_days is not None else None,
                "moq": int(moq) if moq is not None else None,
                "pack_size": int(pack_size) if pack_size is not None else None,
                "estimated_cost": estimated_cost,
                "purchase_price": purchase_price,
                "selling_price": selling_price,
                "supplier_source": supplier_source,
                "purchase_price_source": purchase_price_source,
                "selling_price_source": selling_price_source,
                "lead_time_source": lead_time_source,
                "moq_source": moq_source,
                "pack_size_source": pack_size_source,
            }
        )

    return enriched_items


def _apply_constraints(
    recommended_order_qty: int,
    moq: int | None,
    pack_size: int | None,
) -> tuple[int, str | None]:
    adjusted = max(0, recommended_order_qty)
    reasons: list[str] = []

    if moq is not None and moq > 0 and adjusted < moq:
        adjusted = moq
        reasons.append(f"Увеличено до минимального заказа {moq}")

    if pack_size is not None and pack_size > 1 and adjusted > 0 and adjusted % pack_size != 0:
        adjusted = int(ceil(adjusted / pack_size) * pack_size)
        reasons.append(f"Округлено до кратности упаковки {pack_size}")

    if not reasons:
        return adjusted, "Без дополнительных ограничений"

    return adjusted, ". ".join(reasons)


def _resolve_value(file_value: Any, settings_value: Any) -> tuple[str | None, str]:
    file_text = str(file_value).strip() if file_value not in (None, "") else ""
    settings_text = str(settings_value).strip() if settings_value not in (None, "") else ""

    if settings_text:
        return settings_text, "directory"
    if file_text:
        return file_text, "file"
    return None, "missing"


def _resolve_numeric_value(file_value: Any, settings_value: Any) -> tuple[float | None, str]:
    if settings_value is not None:
        try:
            return float(settings_value), "directory"
        except (TypeError, ValueError):
            pass

    if file_value is not None:
        try:
            return float(file_value), "file"
        except (TypeError, ValueError):
            pass

    return None, "missing"
