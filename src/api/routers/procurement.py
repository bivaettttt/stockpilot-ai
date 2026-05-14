from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.api.procurement import (
    get_sku_setting,
    get_supplier,
    list_sku_settings,
    list_suppliers,
    remove_sku_setting,
    remove_supplier,
    save_sku_setting,
    save_supplier,
)
from src.api.schemas import (
    ProcurementEnrichRequest,
    ProcurementEnrichResponse,
    ProcurementEnrichedItem,
    SkuSettingPayload,
    SkuSettingResponse,
    SkuSettingsListResponse,
    SupplierListResponse,
    SupplierPayload,
    SupplierResponse,
)
from src.services.procurement_service import enrich_procurement_plan

router = APIRouter(tags=["Procurement"])


@router.get("/suppliers", response_model=SupplierListResponse)
def get_suppliers() -> SupplierListResponse:
    return SupplierListResponse(
        status="success",
        suppliers=[SupplierResponse(**item) for item in list_suppliers()],
    )


@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(payload: SupplierPayload) -> SupplierResponse:
    record = save_supplier(
        {
            "id": uuid4().hex[:12],
            **payload.model_dump(),
        }
    )
    return SupplierResponse(**record)


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: str, payload: SupplierPayload) -> SupplierResponse:
    existing = get_supplier(supplier_id)
    if existing is None:
        raise _not_found("Поставщик не найден.")
    record = save_supplier(
        {
            **existing,
            **payload.model_dump(),
            "id": supplier_id,
            "created_at": existing["created_at"],
        }
    )
    return SupplierResponse(**record)


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: str) -> dict[str, str]:
    if not remove_supplier(supplier_id):
        raise _not_found("Поставщик не найден.")
    return {"status": "success"}


@router.get("/sku-settings", response_model=SkuSettingsListResponse)
def get_all_sku_settings() -> SkuSettingsListResponse:
    return SkuSettingsListResponse(
        status="success",
        items=[SkuSettingResponse(**item) for item in list_sku_settings()],
    )


@router.get("/sku-settings/{sku}", response_model=SkuSettingResponse)
def get_single_sku_setting(sku: str) -> SkuSettingResponse:
    record = get_sku_setting(sku)
    if record is None:
        raise _not_found("Настройки товара не найдены.")
    return SkuSettingResponse(**record)


@router.put("/sku-settings/{sku}", response_model=SkuSettingResponse)
def put_sku_setting(sku: str, payload: SkuSettingPayload) -> SkuSettingResponse:
    normalized_sku = sku.strip()
    if not normalized_sku:
        raise HTTPException(status_code=422, detail={"message": "Укажите SKU товара."})

    if payload.supplier_id:
        if get_supplier(payload.supplier_id) is None:
            raise HTTPException(status_code=422, detail={"message": "Выбранный поставщик не найден."})

    record = save_sku_setting({"sku": normalized_sku, **payload.model_dump()})
    return SkuSettingResponse(**record)


@router.delete("/sku-settings/{sku}")
def delete_sku_setting(sku: str) -> dict[str, str]:
    if not remove_sku_setting(sku):
        raise _not_found("Настройки товара не найдены.")
    return {"status": "success"}


@router.post("/procurement/enrich-plan", response_model=ProcurementEnrichResponse)
def post_procurement_enrich_plan(payload: ProcurementEnrichRequest) -> ProcurementEnrichResponse:
    items = enrich_procurement_plan(
        items=[item.model_dump() for item in payload.items],
        suppliers=list_suppliers(),
        sku_settings=list_sku_settings(),
    )
    return ProcurementEnrichResponse(
        items=[ProcurementEnrichedItem(**item) for item in items]
    )


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail={"message": message})
