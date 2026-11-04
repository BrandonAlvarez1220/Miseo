import { UtensilsCrossed } from "lucide-react";
import Link from "next/link";

import { StateMessage } from "@/components/ui/state-message";
import { recipesHref } from "@/features/recipes/search-params";
import { RecipeArt } from "@/features/recipes/recipe-art";
import { pluralize } from "@/lib/format";
import type { Category } from "@/types/api";

export function CategoryGrid({ categories }: { categories: Category[] }) {
  if (categories.length === 0) {
    return (
      <StateMessage
        icon={UtensilsCrossed}
        title="Todavía no hay categorías"
        description="Cuando la comunidad las publique, aparecerán aquí."
      />
    );
  }

  return (
    <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {categories.map((category) => (
        <li key={category.id}>
          <Link
            href={recipesHref({ tipo: category.recipe_type, categoria: category.slug })}
            className="group flex items-center gap-4 rounded-lg border border-line bg-surface p-4 transition-shadow hover:shadow-lift"
          >
            <RecipeArt
              slug={category.slug}
              title={category.name}
              recipeType={category.recipe_type}
              categories={[category]}
              className="size-14 shrink-0 rounded-md"
              iconClassName="size-7"
            />
            <span className="min-w-0">
              <span className="block font-semibold group-hover:text-primary">{category.name}</span>
              <span className="block text-xs text-ink-muted">
                {pluralize(category.recipe_count, "receta", "recetas")}
                {category.description ? ` · ${category.description}` : ""}
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
