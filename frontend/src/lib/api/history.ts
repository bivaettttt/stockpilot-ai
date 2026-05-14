import type {
  AnalyzeResponse,
  HistoryDecisionsResponse,
  HistoryFilesResponse,
  HistoryRecord,
  HistoryResponse,
} from "@/src/types/api";
import { apiRequest } from "@/src/lib/api/client";

type HistoryQuery = {
  page: number;
  pageSize: number;
  originalFilename?: string;
  status?: string;
};

export function getHistoryRequest(query: HistoryQuery) {
  const searchParams = new URLSearchParams({
    page: String(query.page),
    page_size: String(query.pageSize),
  });
  if (query.originalFilename) searchParams.set("original_filename", query.originalFilename);
  if (query.status) searchParams.set("status", query.status);
  return apiRequest<HistoryResponse>(`/history?${searchParams.toString()}`, { retry: 1 });
}

export function getHistoryDetailRequest(runId: string) {
  return apiRequest<HistoryRecord>(`/history/${runId}`, { retry: 1 });
}

export function getHistoryResultRequest(runId: string) {
  return apiRequest<AnalyzeResponse>(`/history/${runId}/result`, { retry: 1 });
}

export function getHistoryFilesRequest(runId: string) {
  return apiRequest<HistoryFilesResponse>(`/history/${runId}/files`, { retry: 1 });
}

export function getHistoryDecisionsRequest(runId: string) {
  return apiRequest<HistoryDecisionsResponse>(`/history/${runId}/decisions`, { retry: 1 });
}

export function putHistoryDecisionsRequest(runId: string, decisions: Record<string, unknown>) {
  return apiRequest<HistoryDecisionsResponse>(`/history/${runId}/decisions`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(decisions),
    retry: 1,
  });
}
