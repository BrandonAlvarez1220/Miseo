import { cookies } from "next/headers";

/** Name of the httpOnly cookie that carries the access token. */
export const SESSION_COOKIE = "miseo_session";

/** The access token of the current request, or undefined when signed out. */
export async function readSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}
