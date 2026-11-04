import { z } from "zod";

import type { MatchMode, RecipeType } from "@/types/api";

/** URL state of /que-puedo-preparar, e.g. ?i=pollo,arroz&modo=flexible&tipo=cooking */
export interface PantryParams {
  ingredients: string[];
  mode: MatchMode;
  recipeType: RecipeType | null;
  assumeStaples: boolean;
}

export const MAX_SELECTED_INGREDIENTS = 40;

const slugList = z
  .string()
  .transform((value) =>
    [...new Set(value.split(",").map((s) => s.trim()))].filter((s) => /^[a-z0-9-]+$/.test(s)),
  )
  .catch([]);

const schema = z.object({
  i: slugList.optional().transform((v) => (v ?? []).slice(0, MAX_SELECTED_INGREDIENTS)),
  modo: z.enum(["exact", "flexible", "discover"]).catch("flexible").default("flexible"),
  tipo: z.enum(["cooking", "drink"]).optional().catch(undefined),
  basicos: z.enum(["0", "1"]).catch("1").default("1"),
});

type RawParams = Record<string, string | string[] | undefined>;

export function parsePantryParams(raw: RawParams | URLSearchParams): PantryParams {
  const entries =
    raw instanceof URLSearchParams
      ? Object.fromEntries(raw.entries())
      : Object.fromEntries(Object.entries(raw).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]));
  const parsed = schema.parse(entries);
  return {
    ingredients: parsed.i,
    mode: parsed.modo,
    recipeType: parsed.tipo ?? null,
    assumeStaples: parsed.basicos === "1",
  };
}

export function pantryHref(params: PantryParams): string {
  const query = new URLSearchParams();
  if (params.ingredients.length) query.set("i", params.ingredients.join(","));
  if (params.mode !== "flexible") query.set("modo", params.mode);
  if (params.recipeType) query.set("tipo", params.recipeType);
  if (!params.assumeStaples) query.set("basicos", "0");
  const qs = query.toString();
  // Commas are safe in query strings and keep shared links readable.
  return qs ? `/que-puedo-preparar?${qs.replaceAll("%2C", ",")}` : "/que-puedo-preparar";
}
