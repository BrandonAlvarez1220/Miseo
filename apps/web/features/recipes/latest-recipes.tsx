import { connection } from "next/server";

import { apiErrorState } from "@/components/ui/api-error-state";
import { attempt } from "@/lib/attempt";
import type { RecipeType } from "@/types/api";

import { searchRecipes } from "./api";
import { RecipeGrid } from "./recipe-grid";

/** Newest published recipes of one module. Render inside <Suspense>. */
export async function LatestRecipes({
  recipeType,
  count = 8,
  retryHref,
}: {
  recipeType: RecipeType;
  count?: number;
  retryHref: string;
}) {
  await connection();
  const result = await attempt(
    searchRecipes({ tipo: recipeType, orden: "newest", porPagina: count }),
  );
  if (!result.ok) return apiErrorState(result.error, retryHref, "las recetas");
  return <RecipeGrid recipes={result.data.items} emptyTitle="Todavía no hay recetas publicadas" />;
}
