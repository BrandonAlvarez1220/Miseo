"use server";

import { z } from "zod";

import { readSessionToken } from "@/features/auth/session";
import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";

import { approveSubmission, rejectSubmission, type ApprovePayload } from "./api";
import { describeDetails } from "./describe-details";

export type ActionResult = { ok: true } | { ok: false; error: string; details: string[] };

const idSchema = z.uuid();

function failure(error: unknown): ActionResult {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return { ok: false, error: "Tu sesión expiró. Vuelve a ingresar.", details: [] };
    }
    if (error.status === 403) {
      return { ok: false, error: "Tu rol no permite hacer esto.", details: [] };
    }
    return { ok: false, error: error.message, details: describeDetails(error.details) };
  }
  console.error("Review action failed", error);
  return { ok: false, error: "Ocurrió un error inesperado. Inténtalo de nuevo.", details: [] };
}

const SIGNED_OUT: ActionResult = {
  ok: false,
  error: "Tu sesión expiró. Vuelve a ingresar.",
  details: [],
};

/** The API validates everything strictly; here we only guard the id and forward. */
export async function approveAction(id: string, payload: ApprovePayload): Promise<ActionResult> {
  if (!idSchema.safeParse(id).success) return { ok: false, error: "Envío inválido.", details: [] };
  const token = await readSessionToken();
  if (!token) return SIGNED_OUT;
  const result = await attempt(approveSubmission(token, id, payload));
  return result.ok ? { ok: true } : failure(result.error);
}

export async function rejectAction(id: string, notes: string): Promise<ActionResult> {
  if (!idSchema.safeParse(id).success) return { ok: false, error: "Envío inválido.", details: [] };
  if (notes.trim().length < 3) {
    return {
      ok: false,
      error: "Escribe el motivo del rechazo (mínimo 3 caracteres).",
      details: [],
    };
  }
  const token = await readSessionToken();
  if (!token) return SIGNED_OUT;
  const result = await attempt(rejectSubmission(token, id, notes.trim()));
  return result.ok ? { ok: true } : failure(result.error);
}
