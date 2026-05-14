import type {
  ProcurementEnrichResponse,
  Recommendation,
  SkuSetting,
  SkuSettingPayload,
  SkuSettingsResponse,
  Supplier,
  SupplierPayload,
  SuppliersResponse,
} from "@/src/types/api";
import { apiRequest } from "@/src/lib/api/client";

export function getSuppliersRequest() {
  return apiRequest<SuppliersResponse>("/suppliers", { retry: 1 });
}

export function createSupplierRequest(payload: SupplierPayload) {
  return apiRequest<Supplier>("/suppliers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateSupplierRequest(supplierId: string, payload: SupplierPayload) {
  return apiRequest<Supplier>(`/suppliers/${supplierId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteSupplierRequest(supplierId: string) {
  return apiRequest<{ status: string }>(`/suppliers/${supplierId}`, {
    method: "DELETE",
  });
}

export function getSkuSettingsRequest() {
  return apiRequest<SkuSettingsResponse>("/sku-settings", { retry: 1 });
}

export function getSkuSettingRequest(sku: string) {
  return apiRequest<SkuSetting>(`/sku-settings/${encodeURIComponent(sku)}`, { retry: 1 });
}

export function putSkuSettingRequest(sku: string, payload: SkuSettingPayload) {
  return apiRequest<SkuSetting>(`/sku-settings/${encodeURIComponent(sku)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteSkuSettingRequest(sku: string) {
  return apiRequest<{ status: string }>(`/sku-settings/${encodeURIComponent(sku)}`, {
    method: "DELETE",
  });
}

export function enrichProcurementPlanRequest(items: Recommendation[]) {
  return apiRequest<ProcurementEnrichResponse>("/procurement/enrich-plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
}
