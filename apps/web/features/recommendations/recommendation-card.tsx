import { ArrowRight, Check, Repeat, ShoppingBasket } from "lucide-react";
import Link from "next/link";

import { recipeHref } from "@/features/recipes/recipe-card";
import { RecipeArt } from "@/features/recipes/recipe-art";
import { RecipeMeta } from "@/features/recipes/recipe-meta";
import { SUBSTITUTION_LABELS } from "@/lib/format";
import type { IngredientRef, Recommendation } from "@/types/api";

import { MatchBadge } from "./match-badge";

function names(items: IngredientRef[]): string {
  return items.map((i) => i.name).join(", ");
}

export function RecommendationCard({ item }: { item: Recommendation }) {
  const { recipe } = item;
  const have = [...item.available_ingredients, ...item.optional_available];
  return (
    <article className="flex h-full flex-col rounded-lg border border-line bg-surface p-4">
      <div className="flex items-start gap-4">
        <RecipeArt
          slug={recipe.slug}
          title={recipe.title}
          recipeType={recipe.recipe_type}
          categories={recipe.categories}
          imageUrl={recipe.image_url}
          className="size-20 shrink-0 rounded-md shadow-soft"
        />
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-pretty">
            <Link href={recipeHref(recipe.slug)} className="hover:text-primary">
              {recipe.title}
            </Link>
          </h3>
          {recipe.categories[0] ? (
            <p className="mt-0.5 text-xs text-ink-muted">{recipe.categories[0].name}</p>
          ) : null}
          <RecipeMeta recipe={recipe} className="mt-2" />
        </div>
        <MatchBadge value={item.match_percentage} />
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        {have.length ? (
          <div className="flex gap-2">
            <dt className="shrink-0">
              <Check aria-hidden="true" className="mt-0.5 size-4 text-primary" />
              <span className="sr-only">Tienes</span>
            </dt>
            <dd className="text-ink-muted">
              <span className="font-medium text-ink">Tienes:</span> {names(have)}
            </dd>
          </div>
        ) : null}
        {item.missing_ingredients.length ? (
          <div className="flex gap-2">
            <dt className="shrink-0">
              <ShoppingBasket aria-hidden="true" className="mt-0.5 size-4 text-accent" />
              <span className="sr-only">Te falta</span>
            </dt>
            <dd className="text-ink-muted">
              <span className="font-medium text-accent-ink">Te falta:</span>{" "}
              {names(item.missing_ingredients)}
            </dd>
          </div>
        ) : null}
        {item.substitutions.map((sub) => (
          <div key={sub.missing.id} className="flex gap-2">
            <dt className="shrink-0">
              <Repeat aria-hidden="true" className="mt-0.5 size-4 text-notice" />
              <span className="sr-only">Sustitución</span>
            </dt>
            <dd className="text-ink-muted">
              Sin <span className="font-medium text-ink">{sub.missing.name}</span>: usa{" "}
              <span className="font-medium text-ink">{sub.substitute.name}</span> (
              {SUBSTITUTION_LABELS[sub.substitution_type]})
            </dd>
          </div>
        ))}
      </dl>

      {item.assumed_staples.length ? (
        <p className="mt-3 text-xs text-ink-muted">
          Damos por hecho que tienes: {names(item.assumed_staples)}.
        </p>
      ) : null}

      <Link
        href={recipeHref(recipe.slug)}
        className="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-semibold text-primary hover:underline"
      >
        Ver receta <ArrowRight aria-hidden="true" className="size-4" />
      </Link>
    </article>
  );
}
