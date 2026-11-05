import { apiFetch } from "@/lib/api-client";
import type { CurrentUser, DevLoginResult } from "@/types/api";

/** Local-development login (the API only exposes it when DEV_LOGIN_ENABLED=true). */
export function devLogin(email: string): Promise<DevLoginResult> {
  return apiFetch<DevLoginResult>("/api/v1/dev/login", {
    init: {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    },
  });
}

export function getMe(token: string): Promise<CurrentUser> {
  return apiFetch<CurrentUser>("/api/v1/me", { token });
}
