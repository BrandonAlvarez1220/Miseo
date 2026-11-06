import Link from "next/link";

import type { RecipeSummary } from "@/types/api";

import { RecipeArt } from "./recipe-art";
import { RecipeMeta } from "./recipe-meta";

export function recipeHref(slug: string): string {
  return `/recetas/${slug}`;
}

export function RecipeCard({ recipe }: { recipe: RecipeSummary }) {
  return (
    <Link
      href={recipeHref(recipe.slug)}
      className="group flex h-full flex-col rounded-lg border border-line bg-surface p-4 transition-shadow hover:shadow-lift"
    >
      <RecipeArt
        slug={recipe.slug}
        title={recipe.title}
        recipeType={recipe.recipe_type}
        categories={recipe.categories}
        imageUrl={recipe.image_url}
        className="size-20 rounded-md shadow-soft"
      />
      <h3 className="mt-4 font-bold text-pretty group-hover:text-primary">{recipe.title}</h3>
      {recipe.categories[0] ? (
        <p className="mt-1 text-xs text-ink-muted">{recipe.categories[0].name}</p>
      ) : null}
      <RecipeMeta recipe={recipe} className="mt-auto pt-4" />
    </Link>
  );
}
