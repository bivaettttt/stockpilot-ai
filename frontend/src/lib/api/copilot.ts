import type {
  AnalysisAssistContext,
  CopilotStatusResponse,
  CopilotMessage,
  CopilotStreamPayload,
  ImportAssistContext,
  ImportAssistResponse,
} from "@/src/types/api";
import { API_URL } from "@/src/lib/constants";
import { ApiError, apiRequest } from "@/src/lib/api/client";

type StreamHandlers = {
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (error: Error) => void;
};

export async function streamCopilot(
  payload: CopilotStreamPayload,
  handlers: StreamHandlers,
  signal?: AbortSignal
) {
  try {
    const response = await fetch(`${API_URL}/copilot/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok || !response.body) {
      throw new Error("Copilot stream unavailable");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      for (const chunk of chunks) {
        const line = chunk.split("\n").find((entry) => entry.startsWith("data: "));
        if (!line) continue;
        const raw = line.slice(6);
        const parsed = JSON.parse(raw) as { type: "token" | "done"; value?: string };
        if (parsed.type === "token" && parsed.value) handlers.onToken(parsed.value);
        if (parsed.type === "done") handlers.onDone();
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    handlers.onError(error instanceof Error ? error : new Error("Stream failed"));
  }
}

const STORAGE_KEY = "stockpilot-copilot-conversation";

export function loadConversation(): CopilotMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as CopilotMessage[];
  } catch {
    return [];
  }
}

export function saveConversation(messages: CopilotMessage[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-40)));
}

export async function requestImportAssist(params: {
  question: string;
  context: ImportAssistContext;
  signal?: AbortSignal;
}): Promise<ImportAssistResponse> {
  const response = await fetch(`${API_URL}/copilot/import-assist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: params.question,
      context: params.context,
    }),
    signal: params.signal,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Import Copilot unavailable", response.status, data);
  }

  return data as ImportAssistResponse;
}

export async function requestAnalysisAssist(params: {
  question: string;
  context: AnalysisAssistContext;
  signal?: AbortSignal;
}): Promise<ImportAssistResponse> {
  const response = await fetch(`${API_URL}/copilot/analysis-assist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: params.question,
      context: params.context,
    }),
    signal: params.signal,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail?.message ?? "Analysis Copilot unavailable", response.status, data);
  }

  return data as ImportAssistResponse;
}

export function getCopilotStatus() {
  return apiRequest<CopilotStatusResponse>("/system/ai-status", { retry: 0, timeoutMs: 6000 });
}
