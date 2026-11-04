import { apiFetch } from "@/lib/api-client";
import type { Ingredient, RecipeType } from "@/types/api";

interface IngredientQuery {
  q?: string;
  slugs?: string[];
  recipeType?: RecipeType;
  includeStaples?: boolean;
  sort?: "name" | "popular";
  limit?: number;
}

export function listIngredients(query: IngredientQuery = {}): Promise<Ingredient[]> {
  return apiFetch<Ingredient[]>("/api/v1/ingredients", {
    query: {
      q: query.q,
      slugs: query.slugs?.length ? query.slugs.join(",") : undefined,
      recipe_type: query.recipeType,
      include_staples: query.includeStaples,
      sort: query.sort,
      limit: query.limit,
    },
  });
}
