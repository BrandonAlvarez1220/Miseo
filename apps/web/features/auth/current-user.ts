import { connection } from "next/server";
import { cache } from "react";

import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";
import type { CurrentUser } from "@/types/api";

import { getMe } from "./api";
import { readSessionToken } from "./session";

export interface Session {
  token: string;
  user: CurrentUser;
}

/**
 * The signed-in user for this request, or null. Memoized per request so the menu
 * and the page share one API call. An expired or invalid token counts as signed out.
 */
export const getSession = cache(async (): Promise<Session | null> => {
  const token = await readSessionToken();
  if (!token) return null;
  // Who the user is belongs to the real request: never resolve it inside the
  // speculative prefetch renders Next runs with real cookies and then aborts.
  await connection();
  const result = await attempt(getMe(token));
  if (result.ok) return { token, user: result.data };
  if (result.error instanceof ApiError && result.error.status === 401) return null;
  // Auth service down or network error: treat as signed out, but leave a trace.
  console.error("Could not load the current user", result.error);
  return null;
});
