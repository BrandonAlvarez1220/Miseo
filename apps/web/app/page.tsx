import { ArrowUpRight, Refrigerator } from "lucide-react";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { buttonVariants } from "@/components/ui/button";
import { chipVariants } from "@/components/ui/chip";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { Skeleton } from "@/components/ui/skeleton";
import { getCategories } from "@/features/categories/api";
import { listIngredients } from "@/features/ingredients/api";
import { searchRecipes } from "@/features/recipes/api";
import { recipeHref } from "@/features/recipes/recipe-card";
import { RecipeArt } from "@/features/recipes/recipe-art";
import { RecipeGrid, RecipeGridSkeleton } from "@/features/recipes/recipe-grid";
import { recipesHref } from "@/features/recipes/search-params";
import { pantryHref } from "@/features/recommendations/search-params";
import { DIFFICULTY_LABELS, formatMinutes, pluralize } from "@/lib/format";
import { attempt } from "@/lib/attempt";
import { cn } from "@/lib/utils";

const EXAMPLE_PANTRY = ["pollo", "arroz", "tomate"];

export default function HomePage() {
  return (
    <>
      <PageHeader
        lead="Recetas desde tu"
        title="propia cocina"
        description="Elige lo que tienes y descubre qué cocinar o qué cóctel preparar. Gratis, abierto y sin depender de la IA."
        actions={
          <Link href="/que-puedo-preparar" className={buttonVariants({ size: "lg" })}>
            <Refrigerator aria-hidden="true" /> Qué puedo preparar
          </Link>
        }
      >
        <Link
          href={pantryHref({
            ingredients: EXAMPLE_PANTRY,
            mode: "flexible",
            recipeType: null,
            assumeStaples: true,
          })}
          className="mt-8 flex items-center justify-between gap-4 rounded-lg bg-notice-soft px-5 py-4 text-sm transition-colors hover:bg-notice-soft/70"
        >
          <span>
            ¿Tienes <span className="font-semibold text-notice">pollo, arroz y tomate</span>? Mira
            lo que puedes cocinar ahora mismo.
          </span>
          <ArrowUpRight aria-hidden="true" className="size-5 shrink-0" />
        </Link>
      </PageHeader>

      <Container className="space-y-14">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <section aria-labelledby="home-recent" className="space-y-5">
            <SectionHeading
              id="home-recent"
              title="Recién añadidas"
              description="Lo último que llegó a la cocina"
              action={<SeeAll href={recipesHref({ tipo: "cooking", orden: "newest" })} />}
            />
            <Suspense fallback={<RecipeGridSkeleton count={4} />}>
              <RecentRecipes />
            </Suspense>
          </section>
          <section aria-labelledby="home-ingredients" className="space-y-5">
            <SectionHeading
              id="home-ingredients"
              title="Ingredientes populares"
              description="Toca uno para ver qué puedes preparar"
              action={<SeeAll href="/que-puedo-preparar" />}
            />
            <Suspense fallback={<Skeleton className="h-64 w-full rounded-lg" />}>
              <PopularIngredients />
            </Suspense>
          </section>
        </div>

        <div className="grid gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <section aria-labelledby="home-bar" className="space-y-5">
            <SectionHeading
              id="home-bar"
              title="Clásicos de la barra"
              description="Cócteles con especificación documentada"
              action={<SeeAll href={recipesHref({ tipo: "drink", categoria: "clasicos" })} />}
            />
            <Suspense fallback={<Skeleton className="h-72 w-full rounded-lg" />}>
              <ClassicsTable />
            </Suspense>
          </section>
          <section aria-labelledby="home-categories" className="space-y-5">
            <SectionHeading
              id="home-categories"
              title="Por categorías"
              description="Las categorías con más recetas"
            />
            <Suspense fallback={<Skeleton className="h-72 w-full rounded-lg" />}>
              <TopCategories />
            </Suspense>
          </section>
        </div>
      </Container>
    </>
  );
}

function SeeAll({ href }: { href: string }) {
  return (
    <Link href={href} className={buttonVariants({ variant: "outline", size: "pill" })}>
      Ver todo
    </Link>
  );
}

async function RecentRecipes() {
  await connection();
  const result = await attempt(searchRecipes({ tipo: "cooking", orden: "newest", porPagina: 4 }));
  if (!result.ok) return apiErrorState(result.error, "/", "las recetas");
  return (
    <div className="[&_ul]:xl:grid-cols-2">
      <RecipeGrid recipes={result.data.items} emptyTitle="Todavía no hay recetas publicadas" />
    </div>
  );
}

async function PopularIngredients() {
  await connection();
  const result = await attempt(
    Promise.all([
      listIngredients({ sort: "popular", includeStaples: false, limit: 16 }),
      searchRecipes({ tipo: "cooking", porPagina: 1 }),
      searchRecipes({ tipo: "drink", porPagina: 1 }),
    ]),
  );
  if (!result.ok) return apiErrorState(result.error, "/", "los ingredientes");
  const [ingredients, cooking, drinks] = result.data;
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Stat
          value={cooking.total}
          label="recetas de cocina"
          href={recipesHref({ tipo: "cooking" })}
        />
        <Stat
          value={drinks.total}
          label="cócteles y bebidas"
          href={recipesHref({ tipo: "drink" })}
        />
      </div>
      <ul className="flex flex-wrap gap-2 rounded-lg border border-line bg-surface p-4">
        {ingredients.map((ingredient) => (
          <li key={ingredient.slug}>
            <Link
              href={pantryHref({
                ingredients: [ingredient.slug],
                mode: "discover",
                recipeType: null,
                assumeStaples: true,
              })}
              className={cn(
                chipVariants({ tone: "neutral", size: "sm" }),
                "border border-line hover:border-primary hover:text-primary",
              )}
            >
              {ingredient.name}
              <span className="text-ink-muted">{ingredient.recipe_count}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Stat({ value, label, href }: { value: number; label: string; href: string }) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-line bg-surface p-4 transition-shadow hover:shadow-lift"
    >
      <span className="block text-2xl font-bold">{value}</span>
      <span className="block text-sm text-ink-muted">{label}</span>
    </Link>
  );
}

async function ClassicsTable() {
  await connection();
  const result = await attempt(
    searchRecipes({ tipo: "drink", categoria: "clasicos", orden: "title", porPagina: 5 }),
  );
  if (!result.ok) return apiErrorState(result.error, "/", "los cócteles");
  const page = result.data;
  if (page.items.length === 0)
    return <p className="text-sm text-ink-muted">Pronto habrá clásicos aquí.</p>;
  return (
    <div className="overflow-x-auto rounded-lg border border-line bg-surface">
      <table className="w-full min-w-[32rem] text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-muted">
            <th scope="col" className="px-4 py-3 font-medium">
              Cóctel
            </th>
            <th scope="col" className="px-4 py-3 font-medium">
              Nivel
            </th>
            <th scope="col" className="px-4 py-3 font-medium">
              Categoría
            </th>
            <th scope="col" className="px-4 py-3 font-medium">
              Tiempo
            </th>
            <th scope="col" className="px-4 py-3">
              <span className="sr-only">Abrir</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {page.items.map((recipe) => (
            <tr key={recipe.id} className="group border-b border-line last:border-0">
              <td className="px-4 py-3">
                <Link
                  href={recipeHref(recipe.slug)}
                  className="flex items-center gap-3 font-medium group-hover:text-primary"
                >
                  <RecipeArt
                    slug={recipe.slug}
                    title={recipe.title}
                    recipeType={recipe.recipe_type}
                    categories={recipe.categories}
                    imageUrl={recipe.image_url}
                    className="size-10 shrink-0 rounded-full"
                    iconClassName="size-5"
                  />
                  {recipe.title}
                </Link>
              </td>
              <td className="px-4 py-3">
                {recipe.difficulty ? DIFFICULTY_LABELS[recipe.difficulty] : "—"}
              </td>
              <td className="px-4 py-3 text-ink-muted">
                {recipe.categories.find((c) => c.slug !== "clasicos")?.name ?? "Clásico"}
              </td>
              <td className="px-4 py-3">{formatMinutes(recipe.total_time_minutes) ?? "—"}</td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={recipeHref(recipe.slug)}
                  aria-label={`Abrir ${recipe.title}`}
                  className="inline-flex size-8 items-center justify-center rounded-full border border-line group-hover:border-accent group-hover:bg-accent group-hover:text-white"
                >
                  <ArrowUpRight aria-hidden="true" className="size-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

async function TopCategories() {
  await connection();
  const result = await attempt(getCategories());
  if (!result.ok) return apiErrorState(result.error, "/", "las categorías");
  const categories = result.data
    .filter((c) => c.recipe_count > 0)
    .sort((a, b) => b.recipe_count - a.recipe_count)
    .slice(0, 3);
  return (
    <div className="space-y-3">
      <ul className="grid grid-cols-3 gap-3">
        {categories.map((category) => (
          <li key={category.id}>
            <Link
              href={recipesHref({ tipo: category.recipe_type, categoria: category.slug })}
              className="group relative block overflow-hidden rounded-lg"
            >
              <RecipeArt
                slug={category.slug}
                title={category.name}
                recipeType={category.recipe_type}
                categories={[category]}
                className="aspect-[3/4] w-full transition-transform group-hover:scale-105"
                iconClassName="size-12 -translate-y-4"
              />
              <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-3 text-white">
                <span className="block text-sm font-bold">{category.name}</span>
                <span className="block text-xs text-white/80">
                  {pluralize(category.recipe_count, "receta", "recetas")}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <Link
        href="/recetas"
        className="flex h-12 items-center justify-center rounded-lg bg-ink text-sm font-semibold text-canvas transition-opacity hover:opacity-90"
      >
        Ver todas las recetas
      </Link>
    </div>
  );
}
