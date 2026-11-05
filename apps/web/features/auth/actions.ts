"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";
import { safeRedirectPath } from "@/lib/safe-redirect";

import { devLogin } from "./api";
import { SESSION_COOKIE } from "./session";

function loginErrorCode(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "disabled";
    if (error.status === 422) return "email";
  }
  return "unavailable";
}

export async function loginAction(formData: FormData): Promise<void> {
  const email = String(formData.get("email") ?? "").trim();
  const next = safeRedirectPath(String(formData.get("next") ?? "/"));

  const result = await attempt(devLogin(email));
  if (!result.ok) {
    redirect(`/ingresar?error=${loginErrorCode(result.error)}&next=${encodeURIComponent(next)}`);
  }

  (await cookies()).set(SESSION_COOKIE, result.data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    // Set SESSION_COOKIE_SECURE=true when serving over HTTPS.
    secure: process.env.SESSION_COOKIE_SECURE === "true",
    path: "/",
    maxAge: result.data.expires_in,
  });
  redirect(next);
}

export async function logoutAction(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
  redirect("/");
}
