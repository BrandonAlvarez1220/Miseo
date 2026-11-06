import { apiFetch } from "@/lib/api-client";
import type { Page, RecipeDetail, RecipeSummary } from "@/types/api";

import type { RecipeSearchParams } from "./search-params";

export function searchRecipes(
  params: Partial<RecipeSearchParams> = {},
): Promise<Page<RecipeSummary>> {
  return apiFetch<Page<RecipeSummary>>("/api/v1/recipes", {
    query: {
      q: params.q,
      recipe_type: params.tipo,
      category: params.categoria,
      difficulty: params.dificultad,
      max_time: params.tiempo,
      sort: params.orden,
      page: params.pagina,
      page_size: params.porPagina,
    },
  });
}

export function getRecipe(slug: string): Promise<RecipeDetail> {
  return apiFetch<RecipeDetail>(`/api/v1/recipes/${encodeURIComponent(slug)}`);
}
