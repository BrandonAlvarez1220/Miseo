"use client";

import { Minus, Plus, Repeat } from "lucide-react";
import { useState } from "react";

import { formatQuantity, parseDecimal, scaleQuantity } from "@/lib/quantity";
import { SUBSTITUTION_LABELS } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { RecipeIngredient } from "@/types/api";

const MAX_SERVINGS = 50;

interface IngredientListProps {
  ingredients: RecipeIngredient[];
  baseServings: number;
  servingLabel: string;
}

/** Ingredient list with a servings stepper that scales every quantity proportionally. */
export function IngredientList({ ingredients, baseServings, servingLabel }: IngredientListProps) {
  const [servings, setServings] = useState(baseServings);
  const groups = groupBy(ingredients);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3 rounded-md bg-surface-muted px-4 py-3">
        <span className="text-sm font-medium" id="servings-label">
          {servingLabel}
        </span>
        <div className="flex items-center gap-3" role="group" aria-labelledby="servings-label">
          <button
            type="button"
            onClick={() => setServings((s) => Math.max(1, s - 1))}
            disabled={servings <= 1}
            aria-label="Menos porciones"
            className="inline-flex size-8 items-center justify-center rounded-full border border-line bg-surface hover:bg-canvas disabled:opacity-40"
          >
            <Minus aria-hidden="true" className="size-4" />
          </button>
          <output aria-live="polite" className="w-6 text-center text-lg font-bold">
            {servings}
          </output>
          <button
            type="button"
            onClick={() => setServings((s) => Math.min(MAX_SERVINGS, s + 1))}
            disabled={servings >= MAX_SERVINGS}
            aria-label="Más porciones"
            className="inline-flex size-8 items-center justify-center rounded-full border border-line bg-surface hover:bg-canvas disabled:opacity-40"
          >
            <Plus aria-hidden="true" className="size-4" />
          </button>
        </div>
      </div>
      {servings !== baseServings ? (
        <p className="mb-3 text-xs text-ink-muted">
          Cantidades ajustadas desde la receta original para {baseServings}.{" "}
          <button
            type="button"
            onClick={() => setServings(baseServings)}
            className="font-medium text-primary hover:underline"
          >
            Restablecer
          </button>
        </p>
      ) : null}

      {groups.map(([label, items]) => (
        <div key={label ?? "default"} className="mb-4 last:mb-0">
          {label ? <h3 className="mb-2 text-sm font-semibold">{label}</h3> : null}
          <ul className="divide-y divide-line">
            {items.map((item) => (
              <IngredientRow
                key={`${item.ingredient.id}-${label ?? ""}`}
                item={item}
                factor={[baseServings, servings]}
              />
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function IngredientRow({
  item,
  factor: [base, servings],
}: {
  item: RecipeIngredient;
  factor: [number, number];
}) {
  const quantity = scaleQuantity(parseDecimal(item.quantity), base, servings);
  const quantityMax = scaleQuantity(parseDecimal(item.quantity_max), base, servings);
  const { amount, unit } = formatQuantity(quantity, quantityMax, item.unit);
  const alternative = item.alternatives[0];
  return (
    <li className="py-3">
      <div className="flex items-baseline gap-3">
        <span
          className={cn(
            "min-w-20 shrink-0 text-sm font-bold",
            !amount && "font-medium text-ink-muted",
          )}
        >
          {amount ? `${amount}${unit ? ` ${unit}` : ""}` : unit}
        </span>
        <span className="text-sm">
          <span className="font-medium">{item.ingredient.name}</span>
          {item.preparation_notes ? (
            <span className="text-ink-muted">, {item.preparation_notes}</span>
          ) : null}
          {item.is_optional ? (
            <span className="ml-2 rounded-full bg-surface-muted px-2 py-0.5 text-[11px] font-medium text-ink-muted">
              opcional
            </span>
          ) : null}
        </span>
      </div>
      {alternative ? (
        <p className="mt-1 flex items-center gap-1.5 pl-23 text-xs text-ink-muted">
          <Repeat aria-hidden="true" className="size-3 text-notice" />
          Sustituye por {alternative.ingredient.name} (
          {SUBSTITUTION_LABELS[alternative.substitution_type]})
          {alternative.notes ? ` · ${alternative.notes}` : ""}
        </p>
      ) : null}
    </li>
  );
}

function groupBy(ingredients: RecipeIngredient[]): [string | null, RecipeIngredient[]][] {
  const groups = new Map<string | null, RecipeIngredient[]>();
  for (const item of ingredients) {
    const list = groups.get(item.group_label) ?? [];
    list.push(item);
    groups.set(item.group_label, list);
  }
  return [...groups.entries()];
}
