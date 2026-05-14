import { API_URL } from "@/src/lib/constants";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

type RequestOptions = RequestInit & {
  timeoutMs?: number;
  retry?: number;
};

function withTimeout(signal: AbortSignal | null | undefined, timeoutMs = 20000) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  return { signal: controller.signal, cleanup: () => window.clearTimeout(timeoutId) };
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs, retry = 1, headers, signal, ...rest } = options;
  let attempt = 0;

  while (attempt <= retry) {
    const timeout = withTimeout(signal, timeoutMs);
    try {
      const response = await fetch(`${API_URL}${path}`, {
        ...rest,
        headers: {
          Accept: "application/json",
          ...(headers ?? {}),
        },
        signal: timeout.signal,
      });

      let data: unknown = null;
      const isJson = response.headers.get("content-type")?.includes("application/json");
      if (isJson) {
        data = await response.json();
      }

      if (!response.ok) {
        const detail = (data as { detail?: { message?: string; errors?: string[] } })?.detail;
        const message = detail?.message ?? `Request failed (${response.status})`;
        throw new ApiError(message, response.status, detail ?? data);
      }

      return data as T;
    } catch (error) {
      if (attempt >= retry || (error instanceof ApiError && error.status < 500)) {
        throw error;
      }
      attempt += 1;
      await new Promise((resolve) => setTimeout(resolve, 250 * attempt));
    } finally {
      timeout.cleanup();
    }
  }

  throw new ApiError("Unknown API error", 500);
}
