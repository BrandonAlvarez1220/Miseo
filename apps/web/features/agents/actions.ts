"use server";

import { z } from "zod";

import { readSessionToken } from "@/features/auth/session";
import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";

import { createAgent, revokeAgent } from "./api";

export type CreateAgentState =
  | { status: "idle" }
  | { status: "error"; error: string }
  | { status: "created"; name: string; token: string };

const createSchema = z.object({
  name: z
    .string()
    .trim()
    .regex(
      /^[A-Za-z0-9][A-Za-z0-9 ._-]{1,59}$/,
      "Usa 2-60 letras, números, espacios, puntos o guiones.",
    ),
  provider: z.enum(["opencode", "claude", "gemini", "other"]),
});

function message(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) return "Ya existe un agente con ese nombre.";
    if (error.status === 401 || error.status === 403)
      return "No tienes permiso o tu sesión expiró.";
    return error.message;
  }
  console.error("Agent action failed", error);
  return "Ocurrió un error inesperado. Inténtalo de nuevo.";
}

export async function createAgentAction(
  _previous: CreateAgentState,
  formData: FormData,
): Promise<CreateAgentState> {
  const parsed = createSchema.safeParse({
    name: formData.get("name"),
    provider: formData.get("provider"),
  });
  if (!parsed.success) {
    return { status: "error", error: parsed.error.issues[0]?.message ?? "Datos inválidos." };
  }
  const token = await readSessionToken();
  if (!token) return { status: "error", error: "Tu sesión expiró. Vuelve a ingresar." };
  const result = await attempt(createAgent(token, parsed.data));
  if (!result.ok) return { status: "error", error: message(result.error) };
  return { status: "created", name: result.data.name, token: result.data.token };
}

export async function revokeAgentAction(id: string): Promise<{ ok: boolean; error?: string }> {
  if (!z.uuid().safeParse(id).success) return { ok: false, error: "Agente inválido." };
  const token = await readSessionToken();
  if (!token) return { ok: false, error: "Tu sesión expiró. Vuelve a ingresar." };
  const result = await attempt(revokeAgent(token, id));
  return result.ok ? { ok: true } : { ok: false, error: message(result.error) };
}
