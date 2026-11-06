import { apiFetch } from "@/lib/api-client";
import type { RecommendationsResponse } from "@/types/api";

import type { PantryParams } from "./search-params";

export function getRecommendations(params: PantryParams): Promise<RecommendationsResponse> {
  return apiFetch<RecommendationsResponse>("/api/v1/recommendations", {
    query: {
      ingredients: params.ingredients.join(","),
      mode: params.mode,
      recipe_type: params.recipeType ?? undefined,
      assume_staples: params.assumeStaples,
      limit: 24,
    },
  });
}
