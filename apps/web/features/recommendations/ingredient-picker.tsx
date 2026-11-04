"use client";

import { Loader2, Plus, Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useOptimistic, useRef, useState, useTransition } from "react";

import { chipVariants } from "@/components/ui/chip";
import { cn } from "@/lib/utils";
import type { Ingredient, IngredientRef, MatchMode, RecipeType } from "@/types/api";

import { MAX_SELECTED_INGREDIENTS, pantryHref, type PantryParams } from "./search-params";

const MODES: { value: MatchMode; label: string; hint: string }[] = [
  { value: "exact", label: "Exacto", hint: "Solo lo que puedes hacer ya mismo" },
  { value: "flexible", label: "Flexible", hint: "Acepta sustituciones conocidas" },
  { value: "discover", label: "Descubrir", hint: "Incluye recetas a las que les falta algo" },
];

const TYPES: { value: RecipeType | null; label: string }[] = [
  { value: null, label: "Todo" },
  { value: "cooking", label: "Cocina" },
  { value: "drink", label: "Bebidas" },
];

interface IngredientPickerProps {
  params: PantryParams;
  selected: IngredientRef[];
  suggestions: Ingredient[];
}

/**
 * Pick ingredients you have. State lives in the URL (shareable, survives
 * reloads); the server renders the matching recipes for that URL.
 */
export function IngredientPicker({ params, selected, suggestions }: IngredientPickerProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [optimistic, setOptimistic] = useOptimistic(selected);

  function navigate(next: Partial<PantryParams>, nextSelected: IngredientRef[] = optimistic) {
    startTransition(() => {
      setOptimistic(nextSelected);
      router.replace(
        pantryHref({ ...params, ...next, ingredients: nextSelected.map((i) => i.slug) }),
        { scroll: false },
      );
    });
  }

  const selectedSlugs = new Set(optimistic.map((i) => i.slug));
  const atLimit = optimistic.length >= MAX_SELECTED_INGREDIENTS;

  function add(ingredient: IngredientRef) {
    if (selectedSlugs.has(ingredient.slug) || atLimit) return;
    navigate({}, [...optimistic, ingredient]);
  }

  function remove(slug: string) {
    navigate(
      {},
      optimistic.filter((i) => i.slug !== slug),
    );
  }

  return (
    <div className="@container space-y-5 rounded-lg border border-line bg-surface p-5">
      <IngredientSearch
        recipeType={params.recipeType}
        exclude={selectedSlugs}
        disabled={atLimit}
        onSelect={add}
      />

      <div>
        <div className="mb-2 flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold">
            Tus ingredientes{" "}
            <span className="font-normal text-ink-muted">({optimistic.length})</span>
          </h2>
          <span className="flex items-center gap-3">
            {pending ? (
              <span className="inline-flex items-center gap-1 text-xs text-ink-muted" role="status">
                <Loader2 aria-hidden="true" className="size-3.5 animate-spin" /> Actualizando…
              </span>
            ) : null}
            {optimistic.length ? (
              <button
                type="button"
                onClick={() => navigate({}, [])}
                className="text-xs font-medium text-ink-muted hover:text-ink"
              >
                Quitar todos
              </button>
            ) : null}
          </span>
        </div>
        {optimistic.length ? (
          <ul className="flex flex-wrap gap-2" aria-label="Ingredientes seleccionados">
            {optimistic.map((ingredient) => (
              <li key={ingredient.slug}>
                <button
                  type="button"
                  onClick={() => remove(ingredient.slug)}
                  className={cn(chipVariants({ tone: "primary" }), "hover:bg-primary/15")}
                  aria-label={`Quitar ${ingredient.name}`}
                >
                  {ingredient.name}
                  <X aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-muted">
            Aún no has elegido nada. Busca arriba o toca alguno de los más usados.
          </p>
        )}
      </div>

      {suggestions.some((s) => !selectedSlugs.has(s.slug)) ? (
        <div>
          <h2 className="mb-2 text-sm font-semibold">Más usados</h2>
          <ul className="flex flex-wrap gap-2" aria-label="Ingredientes sugeridos">
            {suggestions
              .filter((s) => !selectedSlugs.has(s.slug))
              .map((ingredient) => (
                <li key={ingredient.slug}>
                  <button
                    type="button"
                    disabled={atLimit}
                    onClick={() => add(ingredient)}
                    className={cn(
                      chipVariants({ tone: "neutral" }),
                      "border border-line hover:border-primary hover:text-primary disabled:opacity-50",
                    )}
                  >
                    <Plus aria-hidden="true" />
                    {ingredient.name}
                  </button>
                </li>
              ))}
          </ul>
        </div>
      ) : null}

      <div className="grid gap-5 border-t border-line pt-5 @3xl:grid-cols-[1fr_auto]">
        <fieldset>
          <legend className="mb-2 text-sm font-semibold">Modo de búsqueda</legend>
          <div className="grid gap-2 @lg:grid-cols-3">
            {MODES.map((mode) => (
              <button
                key={mode.value}
                type="button"
                aria-pressed={params.mode === mode.value}
                onClick={() => navigate({ mode: mode.value })}
                className={cn(
                  "rounded-md border px-3 py-2 text-left transition-colors",
                  params.mode === mode.value
                    ? "border-primary bg-primary-soft"
                    : "border-line hover:bg-surface-muted",
                )}
              >
                <span
                  className={cn(
                    "block text-sm font-semibold",
                    params.mode === mode.value && "text-primary",
                  )}
                >
                  {mode.label}
                </span>
                <span className="block text-xs text-ink-muted">{mode.hint}</span>
              </button>
            ))}
          </div>
        </fieldset>
        <div className="space-y-3">
          <fieldset>
            <legend className="mb-2 text-sm font-semibold">Mostrar</legend>
            <div className="inline-flex rounded-full bg-surface-muted p-1">
              {TYPES.map((type) => (
                <button
                  key={type.label}
                  type="button"
                  aria-pressed={params.recipeType === type.value}
                  onClick={() => navigate({ recipeType: type.value })}
                  className={cn(
                    "rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors",
                    params.recipeType === type.value
                      ? "bg-surface text-ink shadow-soft"
                      : "text-ink-muted hover:text-ink",
                  )}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={params.assumeStaples}
              onChange={(event) => navigate({ assumeStaples: event.target.checked })}
              className="size-4 accent-[var(--primary)]"
            />
            Tengo lo básico (sal, pimienta, aceite, agua, azúcar)
          </label>
        </div>
      </div>
    </div>
  );
}

interface IngredientSearchProps {
  recipeType: RecipeType | null;
  exclude: Set<string>;
  disabled: boolean;
  onSelect: (ingredient: IngredientRef) => void;
}

/** Accessible combobox (WAI-ARIA 1.2 pattern) with debounced server search. */
function IngredientSearch({ recipeType, exclude, disabled, onSelect }: IngredientSearchProps) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Ingredient[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [activeIndex, setActiveIndex] = useState(0);
  const [open, setOpen] = useState(false);

  const term = query.trim();
  useEffect(() => {
    if (!term) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setStatus("loading");
      try {
        const url = new URLSearchParams({ q: term });
        if (recipeType) url.set("tipo", recipeType);
        const response = await fetch(`/api/ingredients?${url}`, { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        setResults((await response.json()) as Ingredient[]);
        setActiveIndex(0);
        setStatus("idle");
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Ingredient search failed", error);
        setStatus("error");
      }
    }, 200);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [term, recipeType]);

  const options = useMemo(
    () => (term ? results.filter((r) => !exclude.has(r.slug)) : []),
    [term, results, exclude],
  );
  const expanded = open && term.length > 0;

  function choose(ingredient: Ingredient) {
    onSelect(ingredient);
    setQuery("");
    setResults([]);
    setOpen(false);
    inputRef.current?.focus();
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((i) => Math.min(i + 1, Math.max(options.length - 1, 0)));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter") {
      if (expanded && options[activeIndex]) {
        event.preventDefault();
        choose(options[activeIndex]);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="relative">
      <label htmlFor={`${listId}-input`} className="mb-2 block text-sm font-semibold">
        ¿Qué tienes en casa?
      </label>
      <div className="relative">
        <Search
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 left-3.5 size-4.5 -translate-y-1/2 text-ink-muted"
        />
        <input
          ref={inputRef}
          id={`${listId}-input`}
          role="combobox"
          aria-expanded={expanded}
          aria-controls={`${listId}-list`}
          aria-autocomplete="list"
          aria-activedescendant={
            expanded && options[activeIndex] ? `${listId}-${options[activeIndex].slug}` : undefined
          }
          value={query}
          disabled={disabled}
          maxLength={80}
          autoComplete="off"
          placeholder={
            disabled ? "Has alcanzado el máximo de ingredientes" : "Ej. pollo, tomate, lima…"
          }
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={onKeyDown}
          className="h-12 w-full rounded-md border border-line bg-surface pr-4 pl-10 text-sm placeholder:text-ink-muted focus:border-primary focus:outline-none disabled:bg-surface-muted"
        />
      </div>
      {expanded ? (
        <ul
          id={`${listId}-list`}
          role="listbox"
          aria-label="Sugerencias de ingredientes"
          className="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-line bg-surface p-1 shadow-lift"
        >
          {status === "error" ? (
            <li className="px-3 py-2 text-sm text-danger" role="alert">
              No pudimos buscar ingredientes. Inténtalo de nuevo.
            </li>
          ) : options.length === 0 ? (
            <li className="px-3 py-2 text-sm text-ink-muted">
              {status === "loading" ? "Buscando…" : `Sin resultados para “${term}”`}
            </li>
          ) : (
            options.map((option, index) => (
              <li
                key={option.slug}
                id={`${listId}-${option.slug}`}
                role="option"
                aria-selected={index === activeIndex}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(option)}
                onMouseEnter={() => setActiveIndex(index)}
                className={cn(
                  "flex cursor-pointer items-center justify-between rounded px-3 py-2 text-sm",
                  index === activeIndex && "bg-primary-soft text-primary",
                )}
              >
                <span>{option.name}</span>
                <span className="text-xs text-ink-muted">{option.category?.name ?? ""}</span>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
