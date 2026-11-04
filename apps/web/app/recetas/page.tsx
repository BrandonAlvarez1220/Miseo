import { X } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { chipVariants } from "@/components/ui/chip";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Pagination } from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { getCategories } from "@/features/categories/api";
import { searchRecipes } from "@/features/recipes/api";
import { RecipeFilters } from "@/features/recipes/recipe-filters";
import { RecipeGrid, RecipeGridSkeleton } from "@/features/recipes/recipe-grid";
import {
  parseRecipeSearchParams,
  recipesHref,
  type RecipeSearchParams,
} from "@/features/recipes/search-params";
import { DIFFICULTY_LABELS, pluralize } from "@/lib/format";
import type { Category, Page, RecipeSummary } from "@/types/api";

export const metadata: Metadata = {
  title: "Recetas",
  description: "Busca recetas y cócteles por nombre, categoría, tiempo y dificultad.",
};

export default function RecipesPage({ searchParams }: PageProps<"/recetas">) {
  return (
    <>
      <PageHeader
        lead="Explora"
        title="todas las recetas"
        description="Busca por nombre y filtra por categoría, dificultad y tiempo."
      />
      <Container className="space-y-6">
        <Suspense fallback={<ResultsSkeleton />}>
          <Results searchParams={searchParams} />
        </Suspense>
      </Container>
    </>
  );
}

async function Results({ searchParams }: Pick<PageProps<"/recetas">, "searchParams">) {
  // Search results are always fresh: render at request time only.
  await connection();
  const params = parseRecipeSearchParams(await searchParams);
  const pageSize = 12;
  let page: Page<RecipeSummary>;
  let categories: Category[];
  try {
    [page, categories] = await Promise.all([
      searchRecipes({ ...params, porPagina: pageSize }),
      getCategories(),
    ]);
  } catch (error) {
    return apiErrorState(error, recipesHref(params), "las recetas");
  }

  return (
    <>
      <RecipeFilters params={params} categories={categories} />
      <ActiveFilters params={params} categories={categories} />
      <p className="text-sm text-ink-muted" aria-live="polite">
        {pluralize(page.total, "receta encontrada", "recetas encontradas")}
        {params.q ? (
          <>
            {" "}
            para <span className="font-semibold text-ink">“{params.q}”</span>
          </>
        ) : null}
      </p>
      <RecipeGrid recipes={page.items} />
      <Pagination
        page={page.page}
        pages={page.pages}
        hrefFor={(n) => recipesHref({ ...params, pagina: n })}
      />
    </>
  );
}

/** Removable chips for each active filter. */
function ActiveFilters({
  params,
  categories,
}: {
  params: RecipeSearchParams;
  categories: Category[];
}) {
  const category = categories.find((c) => c.slug === params.categoria);
  const active = [
    params.q ? { key: "q", label: `“${params.q}”` } : null,
    params.tipo ? { key: "tipo", label: params.tipo === "drink" ? "Bebidas" : "Cocina" } : null,
    category ? { key: "categoria", label: category.name } : null,
    params.dificultad ? { key: "dificultad", label: DIFFICULTY_LABELS[params.dificultad] } : null,
    params.tiempo ? { key: "tiempo", label: `≤ ${params.tiempo} min` } : null,
  ].filter((item) => item !== null);

  if (active.length === 0) return null;
  return (
    <ul className="flex flex-wrap items-center gap-2" aria-label="Filtros activos">
      {active.map(({ key, label }) => (
        <li key={key}>
          <Link
            href={recipesHref({ ...params, [key]: undefined, pagina: 1 })}
            className={chipVariants({ tone: "primary", size: "sm" })}
            aria-label={`Quitar filtro ${label}`}
          >
            {label} <X aria-hidden="true" />
          </Link>
        </li>
      ))}
      <li>
        <Link href="/recetas" className="text-xs font-medium text-ink-muted hover:text-ink">
          Limpiar todo
        </Link>
      </li>
    </ul>
  );
}

function ResultsSkeleton() {
  return (
    <>
      <Skeleton className="h-24 w-full rounded-lg" />
      <RecipeGridSkeleton />
    </>
  );
}
