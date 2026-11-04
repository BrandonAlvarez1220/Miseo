import { SlidersHorizontal } from "lucide-react";
import Form from "next/form";

import { buttonVariants } from "@/components/ui/button";
import { DIFFICULTY_LABELS } from "@/lib/format";
import type { Category } from "@/types/api";

import { AutoSubmit } from "./auto-submit";
import type { RecipeSearchParams } from "./search-params";

const TIME_OPTIONS = [15, 30, 45, 60, 120];

const SORT_LABELS = {
  relevance: "Más relevantes",
  newest: "Más recientes",
  title: "Alfabético",
  quickest: "Más rápidas",
} as const;

const selectClass =
  "h-10 w-full rounded-md border border-line bg-surface px-3 text-sm focus:border-primary focus:outline-none";

interface RecipeFiltersProps {
  params: RecipeSearchParams;
  categories: Category[];
}

/**
 * Filter bar as a GET form: every combination is a shareable URL and it works
 * without JavaScript (the "Aplicar" button). With JS, changes apply instantly.
 */
export function RecipeFilters({ params, categories }: RecipeFiltersProps) {
  const visibleCategories = params.tipo
    ? categories.filter((c) => c.recipe_type === params.tipo)
    : categories;
  return (
    <Form action="/recetas" className="rounded-lg border border-line bg-surface p-4">
      <AutoSubmit />
      {params.q ? <input type="hidden" name="q" value={params.q} /> : null}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <label className="space-y-1 text-xs font-medium text-ink-muted">
          Tipo
          <select name="tipo" defaultValue={params.tipo ?? ""} className={selectClass}>
            <option value="">Todo</option>
            <option value="cooking">Cocina</option>
            <option value="drink">Bebidas</option>
          </select>
        </label>
        <label className="space-y-1 text-xs font-medium text-ink-muted">
          Categoría
          <select name="categoria" defaultValue={params.categoria ?? ""} className={selectClass}>
            <option value="">Todas</option>
            {visibleCategories.map((category) => (
              <option key={category.id} value={category.slug}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-xs font-medium text-ink-muted">
          Dificultad
          <select name="dificultad" defaultValue={params.dificultad ?? ""} className={selectClass}>
            <option value="">Cualquiera</option>
            {Object.entries(DIFFICULTY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-xs font-medium text-ink-muted">
          Tiempo máximo
          <select name="tiempo" defaultValue={params.tiempo ?? ""} className={selectClass}>
            <option value="">Sin límite</option>
            {TIME_OPTIONS.map((minutes) => (
              <option key={minutes} value={minutes}>
                {minutes < 60 ? `${minutes} min` : `${minutes / 60} h`}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-xs font-medium text-ink-muted">
          Ordenar por
          <select name="orden" defaultValue={params.orden ?? ""} className={selectClass}>
            <option value="">{params.q ? SORT_LABELS.relevance : SORT_LABELS.newest}</option>
            {Object.entries(SORT_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <div className="flex items-end">
          <button type="submit" className={buttonVariants({ className: "w-full" })}>
            <SlidersHorizontal aria-hidden="true" /> Aplicar
          </button>
        </div>
      </div>
    </Form>
  );
}
