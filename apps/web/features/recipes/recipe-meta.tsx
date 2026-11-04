import { ChartNoAxesColumn, Clock3, Users, Wine } from "lucide-react";

import { DIFFICULTY_LABELS, formatMinutes, pluralize } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { RecipeSummary } from "@/types/api";

interface RecipeMetaProps {
  recipe: Pick<
    RecipeSummary,
    "total_time_minutes" | "difficulty" | "servings" | "recipe_type" | "is_alcoholic"
  >;
  showServings?: boolean;
  className?: string;
}

/** Compact metadata row: time · difficulty · servings / alcohol. */
export function RecipeMeta({ recipe, showServings = false, className }: RecipeMetaProps) {
  const time = formatMinutes(recipe.total_time_minutes);
  const items = [
    time ? { icon: Clock3, label: time, tone: "text-accent" } : null,
    recipe.difficulty
      ? {
          icon: ChartNoAxesColumn,
          label: DIFFICULTY_LABELS[recipe.difficulty],
          tone: "text-primary",
        }
      : null,
    showServings
      ? {
          icon: Users,
          label: pluralize(recipe.servings, "porción", "porciones"),
          tone: "text-ink-muted",
        }
      : null,
    recipe.recipe_type === "drink" && recipe.is_alcoholic !== null
      ? {
          icon: Wine,
          label: recipe.is_alcoholic ? "Con alcohol" : "Sin alcohol",
          tone: "text-ink-muted",
        }
      : null,
  ].filter((item) => item !== null);

  return (
    <ul
      className={cn(
        "flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-muted",
        className,
      )}
    >
      {items.map(({ icon: Icon, label, tone }) => (
        <li key={label} className="inline-flex items-center gap-1">
          <Icon aria-hidden="true" className={cn("size-3.5", tone)} />
          {label}
        </li>
      ))}
    </ul>
  );
}
