import type { AnalyzeResponse } from "@/src/types/api";
import { API_URL } from "@/src/lib/constants";
import { ApiError } from "@/src/lib/api/client";

export async function runAnalysisRequest(params: {
  file: File;
  horizon: number;
  safetyStock: number;
  leadTime: number;
  signal?: AbortSignal;
}): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("horizon", String(params.horizon));
  formData.append("safety_stock", String(params.safetyStock));
  formData.append("lead_time", String(params.leadTime));

  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    body: formData,
    signal: params.signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Analysis failed", response.status, data);
  }
  return data as AnalyzeResponse;
}
