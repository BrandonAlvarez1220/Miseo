import { z } from "zod";

/**
 * Query string of /recetas (user-facing, so in Spanish). Invalid values are
 * dropped instead of failing: a hand-edited URL still shows results.
 */
const optional = <T extends z.ZodType>(schema: T) => schema.optional().catch(undefined);

export const recipeSearchParamsSchema = z.object({
  q: optional(z.string().trim().min(1).max(100)),
  tipo: optional(z.enum(["cooking", "drink"])),
  categoria: optional(
    z
      .string()
      .regex(/^[a-z0-9-]+$/)
      .max(100),
  ),
  dificultad: optional(z.enum(["easy", "medium", "hard"])),
  tiempo: optional(z.coerce.number().int().min(1).max(1440)),
  orden: optional(z.enum(["relevance", "newest", "title", "quickest"])),
  pagina: z.coerce.number().int().min(1).max(1000).catch(1).default(1),
  porPagina: optional(z.coerce.number().int().min(1).max(48)),
});

export type RecipeSearchParams = z.infer<typeof recipeSearchParamsSchema>;

type RawParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function parseRecipeSearchParams(raw: RawParams): RecipeSearchParams {
  const flat = Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, first(value)]));
  return recipeSearchParamsSchema.parse(flat);
}

/** Build a /recetas URL, dropping empty values and resetting to page 1 unless given. */
export function recipesHref(params: Partial<RecipeSearchParams>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (key === "pagina" && value === 1) continue;
    query.set(key, String(value));
  }
  const qs = query.toString();
  return qs ? `/recetas?${qs}` : "/recetas";
}
