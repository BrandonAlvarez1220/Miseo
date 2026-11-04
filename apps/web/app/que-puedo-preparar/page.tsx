import { ChefHat, Lightbulb, Refrigerator } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StateMessage } from "@/components/ui/state-message";
import { listIngredients } from "@/features/ingredients/api";
import { RecipeGridSkeleton } from "@/features/recipes/recipe-grid";
import { getRecommendations } from "@/features/recommendations/api";
import { IngredientPicker } from "@/features/recommendations/ingredient-picker";
import { RecommendationCard } from "@/features/recommendations/recommendation-card";
import {
  pantryHref,
  parsePantryParams,
  type PantryParams,
} from "@/features/recommendations/search-params";
import { pluralize } from "@/lib/format";
import type { Ingredient, RecommendationsResponse } from "@/types/api";

export const metadata: Metadata = {
  title: "Qué puedo preparar",
  description: "Elige los ingredientes que tienes y descubre qué recetas y cócteles puedes hacer.",
};

export default function PantryPage({ searchParams }: PageProps<"/que-puedo-preparar">) {
  return (
    <>
      <PageHeader
        lead="¿Qué puedo preparar"
        title="con lo que tengo?"
        description="Elige tus ingredientes y te mostramos las recetas ordenadas por compatibilidad, con lo que te falta y cómo sustituirlo."
      />
      <Container>
        <Suspense fallback={<WorkspaceSkeleton />}>
          <Workspace searchParams={searchParams} />
        </Suspense>
      </Container>
    </>
  );
}

async function Workspace({ searchParams }: Pick<PageProps<"/que-puedo-preparar">, "searchParams">) {
  await connection();
  const params = parsePantryParams(await searchParams);
  let selected: Ingredient[];
  let suggestions: Ingredient[];
  try {
    [selected, suggestions] = await Promise.all([
      params.ingredients.length
        ? listIngredients({ slugs: params.ingredients, limit: params.ingredients.length })
        : Promise.resolve([]),
      listIngredients({
        sort: "popular",
        includeStaples: false,
        recipeType: params.recipeType ?? undefined,
        limit: 14,
      }),
    ]);
  } catch (error) {
    return apiErrorState(error, pantryHref(params), "los ingredientes");
  }
  // Keep the user's selection order.
  const order = new Map(params.ingredients.map((slug, index) => [slug, index]));
  selected.sort((a, b) => (order.get(a.slug) ?? 0) - (order.get(b.slug) ?? 0));

  return (
    <div className="grid gap-8 xl:grid-cols-[minmax(0,26rem)_1fr]">
      <div className="xl:sticky xl:top-24 xl:self-start">
        <IngredientPicker params={params} selected={selected} suggestions={suggestions} />
      </div>
      <section aria-labelledby="pantry-results" className="min-w-0">
        <h2 id="pantry-results" className="sr-only">
          Recetas compatibles
        </h2>
        <Suspense key={pantryHref(params)} fallback={<RecipeGridSkeleton count={4} />}>
          <Results params={params} />
        </Suspense>
      </section>
    </div>
  );
}

async function Results({ params }: { params: PantryParams }) {
  if (params.ingredients.length === 0) {
    return (
      <StateMessage
        icon={Refrigerator}
        title="Empieza por tus ingredientes"
        description="Añade lo que tienes en la nevera o en la despensa. Con dos o tres ingredientes ya podemos sugerirte algo."
      />
    );
  }

  let data: RecommendationsResponse;
  try {
    data = await getRecommendations(params);
  } catch (error) {
    return apiErrorState(error, pantryHref(params), "las recomendaciones");
  }

  return (
    <div className="space-y-4">
      {data.unknown_ingredients.length ? (
        <p className="rounded-md bg-notice-soft px-4 py-3 text-sm" role="status">
          No reconocemos: {data.unknown_ingredients.join(", ")}. Puede que el enlace sea antiguo.
        </p>
      ) : null}
      {data.results.length === 0 ? (
        <NoResults params={params} />
      ) : (
        <>
          <p className="text-sm text-ink-muted" aria-live="polite">
            {pluralize(data.total, "receta compatible", "recetas compatibles")}
            {data.total > data.results.length
              ? ` · mostrando las ${data.results.length} mejores`
              : ""}
          </p>
          <ul className="grid gap-4 lg:grid-cols-2">
            {data.results.map((item) => (
              <li key={item.recipe.id}>
                <RecommendationCard item={item} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function NoResults({ params }: { params: PantryParams }) {
  const wider =
    params.mode === "exact" ? "flexible" : params.mode === "flexible" ? "discover" : null;
  return (
    <StateMessage
      icon={params.mode === "discover" ? ChefHat : Lightbulb}
      title={
        params.mode === "exact"
          ? "Aún no hay recetas que puedas hacer solo con eso"
          : "No encontramos recetas con esos ingredientes"
      }
      description={
        wider
          ? "Prueba un modo más amplio: te mostraremos opciones con sustituciones o con algún ingrediente pendiente."
          : "Prueba con otros ingredientes o quita el filtro de tipo."
      }
      action={
        wider ? (
          <Link
            href={pantryHref({ ...params, mode: wider })}
            className="text-sm font-semibold text-primary hover:underline"
          >
            Probar modo {wider === "flexible" ? "Flexible" : "Descubrir"}
          </Link>
        ) : null
      }
    />
  );
}

function WorkspaceSkeleton() {
  return (
    <div className="grid gap-8 xl:grid-cols-[minmax(0,26rem)_1fr]">
      <Skeleton className="h-96 w-full rounded-lg" />
      <RecipeGridSkeleton count={4} />
    </div>
  );
}
