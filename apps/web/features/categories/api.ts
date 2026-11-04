import { apiFetch } from "@/lib/api-client";
import type { Category, RecipeType } from "@/types/api";

export function getCategories(recipeType?: RecipeType): Promise<Category[]> {
  return apiFetch<Category[]>("/api/v1/categories", { query: { recipe_type: recipeType } });
}
