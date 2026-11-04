import { CloudOff } from "lucide-react";
import { connection } from "next/server";

import { buttonVariants } from "@/components/ui/button";
import { StateMessage } from "@/components/ui/state-message";
import { ApiError } from "@/lib/api-client";
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
    if (!(error instanceof ApiError)) throw error;
    console.error("Failed to load categories", { code: error.code, status: error.status });
    return (
      <StateMessage
        tone="danger"
        icon={CloudOff}
        title="No pudimos cargar las categorías"
        description="El servicio no está disponible en este momento. Inténtalo de nuevo en unos segundos."
        action={
          <a href={retryHref} className={buttonVariants({ variant: "secondary", size: "sm" })}>
            Reintentar
          </a>
        }
      />
    );
  }
  return <CategoryGrid categories={categories} />;
}
