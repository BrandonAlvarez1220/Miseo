import { apiFetch } from "@/lib/api-client";
import type { Agent, AgentProvider, CreatedAgent } from "@/types/api";

export function listAgents(token: string): Promise<Agent[]> {
  return apiFetch<Agent[]>("/api/v1/admin/agents", { token });
}

export function createAgent(
  token: string,
  body: { name: string; provider: AgentProvider; description?: string },
): Promise<CreatedAgent> {
  return apiFetch<CreatedAgent>("/api/v1/admin/agents", {
    token,
    init: {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  });
}

export function revokeAgent(token: string, id: string): Promise<Agent> {
  return apiFetch<Agent>(`/api/v1/admin/agents/${encodeURIComponent(id)}/revoke`, {
    token,
    init: { method: "POST" },
  });
}
