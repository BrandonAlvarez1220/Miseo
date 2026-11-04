import { UtensilsCrossed } from "lucide-react";

import { StateMessage } from "@/components/ui/state-message";
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
        <li key={category.id} className="rounded-lg border border-line bg-surface p-5">
          <p className="font-semibold">{category.name}</p>
          {category.description ? (
            <p className="mt-1 text-sm text-ink-muted">{category.description}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
