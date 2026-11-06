import {
  BookOpenText,
  ChartNoAxesColumn,
  Clock3,
  CookingPot,
  ExternalLink,
  GlassWater,
  Lightbulb,
  Sparkles,
  Timer,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense, type ReactNode } from "react";

import { MixologyRegion } from "@/components/layout/theme-region";
import { apiErrorState } from "@/components/ui/api-error-state";
import { Chip } from "@/components/ui/chip";
import { Container } from "@/components/ui/container";
import { SectionHeading } from "@/components/ui/section-heading";
import { Skeleton } from "@/components/ui/skeleton";
import { CocktailAnimation } from "@/features/cocktail/cocktail-animation";
import { RecipeLearning } from "@/features/paths/recipe-learning";
import { getRecipe } from "@/features/recipes/api";
import { IngredientList } from "@/features/recipes/ingredient-list";
import { RecipeArt } from "@/features/recipes/recipe-art";
import { RecipeGrid } from "@/features/recipes/recipe-grid";
import { recipesHref } from "@/features/recipes/search-params";
import { ShareButton } from "@/features/recipes/share-button";
import { ApiError } from "@/lib/api-client";
import { CLASSIFICATION_LABELS, DIFFICULTY_LABELS, formatMinutes } from "@/lib/format";
import type { DrinkDetails, RecipeDetail } from "@/types/api";

async function loadRecipe(slug: string): Promise<RecipeDetail> {
  try {
    return await getRecipe(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
}

export async function generateMetadata({
  params,
}: PageProps<"/recetas/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  try {
    const recipe = await getRecipe(slug);
    return { title: recipe.title, description: recipe.description ?? undefined };
  } catch {
    // The page itself renders the proper 404 / error state.
    return { title: "Receta" };
  }
}

export default function RecipePage({ params }: PageProps<"/recetas/[slug]">) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <RecipeView params={params} />
    </Suspense>
  );
}

async function RecipeView({ params }: Pick<PageProps<"/recetas/[slug]">, "params">) {
  await connection();
  const { slug } = await params;
  let recipe: RecipeDetail;
  try {
    recipe = await loadRecipe(slug);
  } catch (error) {
    return (
      <Container className="py-10">
        {apiErrorState(error, `/recetas/${slug}`, "la receta")}
      </Container>
    );
  }
  const content = <RecipeContent recipe={recipe} />;
  return recipe.recipe_type === "drink" ? (
    <MixologyRegion className="min-h-full pb-12">{content}</MixologyRegion>
  ) : (
    content
  );
}

function RecipeContent({ recipe }: { recipe: RecipeDetail }) {
  const isDrink = recipe.recipe_type === "drink";
  return (
    <article>
      <Container className="pt-6 pb-10 sm:pt-10">
        <nav aria-label="Ruta" className="mb-6 text-sm text-ink-muted">
          <Link href={recipesHref({ tipo: recipe.recipe_type })} className="hover:text-ink">
            {isDrink ? "Mixología" : "Cocina"}
          </Link>
          {recipe.categories[0] ? (
            <>
              {" / "}
              <Link
                href={recipesHref({
                  tipo: recipe.recipe_type,
                  categoria: recipe.categories[0].slug,
                })}
                className="hover:text-ink"
              >
                {recipe.categories[0].name}
              </Link>
            </>
          ) : null}
        </nav>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start">
          {isDrink && recipe.drink ? (
            <CocktailAnimation
              title={recipe.title}
              drink={recipe.drink}
              ingredients={recipe.ingredients}
            />
          ) : (
            <RecipeArt
              slug={recipe.slug}
              title={recipe.title}
              recipeType={recipe.recipe_type}
              categories={recipe.categories}
              imageUrl={recipe.image_url}
              className="aspect-[4/3] w-full rounded-xl"
              iconClassName="size-24"
            />
          )}
          <div>
            <ul className="mb-4 flex flex-wrap gap-2">
              {isDrink && recipe.drink ? (
                <li>
                  <Chip tone="accent" size="sm">
                    <Sparkles aria-hidden="true" />
                    {CLASSIFICATION_LABELS[recipe.drink.classification]}
                  </Chip>
                </li>
              ) : null}
              {recipe.categories.map((category) => (
                <li key={category.slug}>
                  <Link href={recipesHref({ tipo: recipe.recipe_type, categoria: category.slug })}>
                    <Chip tone="primary" size="sm" className="hover:opacity-80">
                      {category.name}
                    </Chip>
                  </Link>
                </li>
              ))}
            </ul>
            <h1 className="text-3xl font-bold tracking-tight text-balance sm:text-5xl">
              {recipe.title}
            </h1>
            {recipe.description ? (
              <p className="mt-4 text-lg text-pretty text-ink-muted">{recipe.description}</p>
            ) : null}
            {isDrink && recipe.drink?.variation_of ? (
              <p className="mt-3 text-sm text-ink-muted">
                Variación de{" "}
                <Link
                  href={`/recetas/${recipe.drink.variation_of.slug}`}
                  className="font-semibold text-primary hover:underline"
                >
                  {recipe.drink.variation_of.title}
                </Link>
              </p>
            ) : null}
            <dl className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Fact
                icon={<Timer />}
                label="Preparación"
                value={formatMinutes(recipe.preparation_time_minutes)}
              />
              <Fact
                icon={<CookingPot />}
                label="Cocción"
                // "0 min" of cooking (salads, cocktails) is noise: hide it.
                value={
                  recipe.cooking_time_minutes ? formatMinutes(recipe.cooking_time_minutes) : null
                }
              />
              <Fact
                icon={<Clock3 />}
                label="Total"
                value={formatMinutes(recipe.total_time_minutes)}
              />
              <Fact
                icon={<ChartNoAxesColumn />}
                label="Dificultad"
                value={recipe.difficulty ? DIFFICULTY_LABELS[recipe.difficulty] : null}
              />
            </dl>
            <div className="mt-6">
              <ShareButton title={recipe.title} />
            </div>
          </div>
        </div>
      </Container>

      <Container className="grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <section aria-labelledby="ingredients" className="lg:sticky lg:top-24 lg:self-start">
          <div className="rounded-lg border border-line bg-surface p-5">
            <h2 id="ingredients" className="mb-4 text-xl font-bold">
              Ingredientes
            </h2>
            <IngredientList
              ingredients={recipe.ingredients}
              baseServings={recipe.servings}
              servingLabel={isDrink ? "Bebidas" : "Porciones"}
            />
          </div>
        </section>

        <div className="space-y-10">
          {recipe.introduction ? <p className="text-pretty">{recipe.introduction}</p> : null}

          {isDrink && recipe.drink ? <DrinkPanel drink={recipe.drink} /> : null}

          <section aria-labelledby="steps">
            <h2 id="steps" className="mb-4 text-xl font-bold">
              Preparación
            </h2>
            <ol className="space-y-5">
              {recipe.steps.map((step) => (
                <li key={step.step_number} className="flex gap-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-ink">
                    {step.step_number}
                  </span>
                  <p className="pt-1 text-pretty">{step.description}</p>
                </li>
              ))}
            </ol>
          </section>

          <RecipeLearning recipe={recipe} />

          {recipe.tips ? (
            <aside className="flex gap-3 rounded-lg bg-notice-soft p-5">
              <Lightbulb aria-hidden="true" className="size-5 shrink-0 text-notice" />
              <div>
                <h2 className="font-semibold">Consejo</h2>
                <p className="mt-1 text-sm text-pretty">{recipe.tips}</p>
              </div>
            </aside>
          ) : null}

          <section aria-labelledby="sources" className="rounded-lg border border-line p-5">
            <h2 id="sources" className="mb-3 flex items-center gap-2 font-semibold">
              <BookOpenText aria-hidden="true" className="size-4.5 text-ink-muted" />
              Fuente y atribución
            </h2>
            <ul className="space-y-3 text-sm">
              {recipe.sources.map((source) => (
                <li key={source.source_name}>
                  <p className="font-medium">
                    {source.source_url ? (
                      <a
                        href={source.source_url}
                        target="_blank"
                        rel="noreferrer nofollow"
                        className="inline-flex items-center gap-1 hover:text-primary"
                      >
                        {source.source_name}
                        <ExternalLink aria-hidden="true" className="size-3.5" />
                      </a>
                    ) : (
                      source.source_name
                    )}
                    {source.license ? (
                      <span className="font-normal text-ink-muted"> · {source.license}</span>
                    ) : null}
                  </p>
                  {source.attribution ? (
                    <p className="text-ink-muted">{source.attribution}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </Container>

      {recipe.related.length ? (
        <Container className="mt-16 space-y-5">
          <SectionHeading
            title={isDrink ? "Cócteles relacionados" : "Recetas relacionadas"}
            description="Comparten ingredientes o categoría"
          />
          <RecipeGrid recipes={recipe.related} />
        </Container>
      ) : null}
    </article>
  );
}

function DrinkPanel({ drink }: { drink: DrinkDetails }) {
  const facts = [
    drink.glass
      ? { label: "Cristalería", value: drink.glass.name, hint: drink.glass.description }
      : null,
    drink.technique
      ? { label: "Técnica", value: drink.technique.name, hint: drink.technique.description }
      : null,
    drink.base_spirit
      ? { label: "Destilado base", value: drink.base_spirit.name, hint: null }
      : null,
    drink.garnish ? { label: "Guarnición", value: drink.garnish, hint: null } : null,
  ].filter((fact) => fact !== null);
  return (
    <section aria-labelledby="bar" className="rounded-lg border border-line bg-surface p-5">
      <h2 id="bar" className="mb-4 flex items-center gap-2 text-xl font-bold">
        <GlassWater aria-hidden="true" className="size-5 text-primary" />
        En la barra
      </h2>
      <dl className="grid gap-4 sm:grid-cols-2">
        {facts.map((fact) => (
          <div key={fact.label}>
            <dt className="text-xs font-semibold tracking-wide text-ink-muted uppercase">
              {fact.label}
            </dt>
            <dd className="mt-1 font-medium">{fact.value}</dd>
            {fact.hint ? <dd className="mt-0.5 text-xs text-ink-muted">{fact.hint}</dd> : null}
          </div>
        ))}
      </dl>
      {drink.variations.length ? (
        <p className="mt-4 border-t border-line pt-4 text-sm text-ink-muted">
          Variaciones documentadas:{" "}
          {drink.variations.map((variation, index) => (
            <span key={variation.slug}>
              {index > 0 ? ", " : ""}
              <Link
                href={`/recetas/${variation.slug}`}
                className="font-semibold text-primary hover:underline"
              >
                {variation.title}
              </Link>
            </span>
          ))}
        </p>
      ) : null}
    </section>
  );
}

function Fact({ icon, label, value }: { icon: ReactNode; label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="rounded-md border border-line bg-surface px-3 py-2.5 [&_svg]:size-4 [&_svg]:text-accent">
      <dt className="flex items-center gap-1.5 text-xs text-ink-muted">
        {icon}
        {label}
      </dt>
      <dd className="mt-1 font-semibold">{value}</dd>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <Container className="pt-10">
      <div className="grid gap-8 lg:grid-cols-[5fr_6fr]">
        <Skeleton className="aspect-[4/3] w-full rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-12 w-3/4" />
          <Skeleton className="h-5 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      </div>
    </Container>
  );
}
