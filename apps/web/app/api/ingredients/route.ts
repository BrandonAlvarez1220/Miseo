import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { listIngredients } from "@/features/ingredients/api";
import { ApiError } from "@/lib/api-client";

/**
 * Backend-for-frontend proxy for ingredient autocomplete. The browser talks to
 * this route; only the Next.js server knows API_URL. Only whitelisted, validated
 * parameters are forwarded.
 */
const querySchema = z.object({
  q: z.string().trim().min(1).max(80),
  tipo: z.enum(["cooking", "drink"]).optional(),
});

export async function GET(request: NextRequest) {
  const parsed = querySchema.safeParse(Object.fromEntries(request.nextUrl.searchParams));
  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: "validation_error", message: "Parámetros inválidos", details: null } },
      { status: 422 },
    );
  }
  try {
    const ingredients = await listIngredients({
      q: parsed.data.q,
      recipeType: parsed.data.tipo,
      limit: 8,
    });
    return NextResponse.json(ingredients);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    console.error("Ingredient autocomplete failed", { code: error.code, status: error.status });
    return NextResponse.json(
      { error: { code: error.code, message: "No se pudo buscar ingredientes", details: null } },
      { status: 502 },
    );
  }
}
