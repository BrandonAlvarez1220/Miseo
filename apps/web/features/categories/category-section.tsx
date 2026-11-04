import { connection } from "next/server";

import { apiErrorState } from "@/components/ui/api-error-state";
import type { Category, RecipeType } from "@/types/api";

import { getCategories } from "./api";
import { CategoryGrid } from "./category-grid";

interface CategorySectionProps {
  recipeType: RecipeType;
  /** Path to reload when the user retries after an error. */
  retryHref: string;
}

/** Fetches categories at request time; render inside <Suspense>. */
export async function CategorySection({ recipeType, retryHref }: CategorySectionProps) {
  // Catalog data must be fresh: defer to request time instead of prerendering
  // (the API is not necessarily reachable at build time).
  await connection();
  let categories: Category[];
  try {
    categories = await getCategories(recipeType);
  } catch (error) {
    return apiErrorState(error, retryHref, "las categorías");
  }
  return <CategoryGrid categories={categories} />;
}
