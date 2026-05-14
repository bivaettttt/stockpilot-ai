import type {
  ImportInspectResponse,
  SuggestMappingResponse,
  ValidateFileResponse,
  ValidateMappingResponse,
} from "@/src/types/api";
import { API_URL } from "@/src/lib/constants";
import { ApiError } from "@/src/lib/api/client";

export async function uploadAndValidate(file: File, signal?: AbortSignal): Promise<ValidateFileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/validate-file`, {
    method: "POST",
    body: formData,
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Validation failed", response.status, data);
  }
  return data as ValidateFileResponse;
}

export async function inspectImportFile(file: File, signal?: AbortSignal): Promise<ImportInspectResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/import/inspect`, {
    method: "POST",
    body: formData,
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Import inspection failed", response.status, data);
  }
  return data as ImportInspectResponse;
}

export async function downloadDemoFile(signal?: AbortSignal): Promise<File> {
  const response = await fetch(`${API_URL}/files/demo`, { signal });
  if (!response.ok) {
    throw new ApiError("Не удалось получить demo-файл.", response.status);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("content-disposition") ?? "";
  const matchedFilename = contentDisposition.match(/filename="?([^"]+)"?/i)?.[1];
  const filename = matchedFilename || "sample_sales.csv";

  return new File([blob], filename, { type: "text/csv" });
}

export async function suggestImportMapping(file: File, signal?: AbortSignal): Promise<SuggestMappingResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/import/suggest-mapping`, {
    method: "POST",
    body: formData,
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Mapping suggestion failed", response.status, data);
  }
  return data as SuggestMappingResponse;
}

export async function validateImportMapping(params: {
  file: File;
  mapping: Record<string, { source_column: string | null; confidence?: number; status?: string }>;
  signal?: AbortSignal;
}): Promise<ValidateMappingResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("mapping", JSON.stringify(params.mapping));
  const response = await fetch(`${API_URL}/import/validate-mapping`, {
    method: "POST",
    body: formData,
    signal: params.signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Mapping validation failed", response.status, data);
  }
  return data as ValidateMappingResponse;
}

export async function normalizeImportFile(params: {
  file: File;
  mapping: Record<string, { source_column: string | null; confidence?: number; status?: string }>;
  signal?: AbortSignal;
}): Promise<File> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("mapping", JSON.stringify(params.mapping));
  const response = await fetch(`${API_URL}/import/normalize`, {
    method: "POST",
    body: formData,
    signal: params.signal,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(data?.detail?.message ?? "Normalization failed", response.status, data);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("content-disposition") ?? "";
  const matchedFilename = contentDisposition.match(/filename="?([^"]+)"?/i)?.[1];
  const filename = matchedFilename || "normalized.csv";
  return new File([blob], filename, { type: "text/csv" });
}
