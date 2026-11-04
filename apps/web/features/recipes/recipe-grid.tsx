import { SearchX } from "lucide-react";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { StateMessage } from "@/components/ui/state-message";
import type { RecipeSummary } from "@/types/api";

import { RecipeCard } from "./recipe-card";

interface RecipeGridProps {
  recipes: RecipeSummary[];
  emptyTitle?: string;
  emptyDescription?: ReactNode;
}

export function RecipeGrid({
  recipes,
  emptyTitle = "No encontramos recetas",
  emptyDescription = "Prueba con otros filtros o con menos palabras.",
}: RecipeGridProps) {
  if (recipes.length === 0) {
    return <StateMessage icon={SearchX} title={emptyTitle} description={emptyDescription} />;
  }
  return (
    <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {recipes.map((recipe) => (
        <li key={recipe.id}>
          <RecipeCard recipe={recipe} />
        </li>
      ))}
    </ul>
  );
}

export function RecipeGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div role="status" aria-label="Cargando recetas">
      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: count }, (_, index) => (
          <li key={index} className="rounded-lg border border-line bg-surface p-4">
            <Skeleton className="size-20" />
            <Skeleton className="mt-4 h-5 w-3/4" />
            <Skeleton className="mt-2 h-3 w-1/3" />
            <Skeleton className="mt-5 h-3 w-2/3" />
          </li>
        ))}
      </ul>
    </div>
  );
}
