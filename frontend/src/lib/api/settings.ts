import type { WorkspaceSettings, WorkspaceSettingsResponse } from "@/src/types/api";
import { apiRequest } from "@/src/lib/api/client";

export function getSettings() {
  return apiRequest<WorkspaceSettingsResponse>("/settings", { retry: 1 });
}

export function updateSettings(payload: Partial<WorkspaceSettings>) {
  return apiRequest<WorkspaceSettingsResponse>("/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
    retry: 1,
  });
}
