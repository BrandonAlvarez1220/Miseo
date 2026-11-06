"use client";

import { Lock, Sparkles, Trophy } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

import { RecipeArt } from "@/features/recipes/recipe-art";
import { recipeHref } from "@/features/recipes/recipe-card";
import { RecipeMeta } from "@/features/recipes/recipe-meta";
import { pluralize } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PathDetail, PathStage } from "@/types/api";

import { CookedToggle } from "./cooked-toggle";
import { computeLadder, type StageProgress } from "./ladder";
import { useCookedRecipes } from "./progress";

export function PathLadder({ path }: { path: PathDetail }) {
  const cookedMap = useCookedRecipes();
  const cooked = useMemo(() => new Set(cookedMap.keys()), [cookedMap]);
  const ladder = computeLadder(path, cooked);
  const percent = ladder.totalDishes
    ? Math.round((ladder.cookedDishes / ladder.totalDishes) * 100)
    : 0;
  const isDrink = path.discipline === "drink";

  return (
    <div className="space-y-8">
      <section
        aria-label="Tu progreso"
        className="grid gap-4 rounded-lg border border-line bg-surface p-5 md:grid-cols-[auto_1fr]"
      >
        <div className="flex items-center gap-4">
          <span className="inline-flex size-14 items-center justify-center rounded-full bg-accent-soft text-accent">
            <Trophy aria-hidden="true" className="size-7" />
          </span>
          <div>
            <p className="text-2xl font-bold">
              {ladder.cookedDishes}
              <span className="text-base font-medium text-ink-muted"> / {ladder.totalDishes}</span>
            </p>
            <p className="text-sm text-ink-muted">
              {isDrink ? "tragos preparados" : "platillos cocinados"} · etapa {ladder.currentStage}
            </p>
          </div>
        </div>
        <div className="min-w-0 space-y-3">
          <div
            className="h-2.5 overflow-hidden rounded-full bg-surface-muted"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            aria-label="Progreso de la ruta"
          >
            <div
              className="h-full rounded-full bg-primary transition-[width]"
              style={{ width: `${percent}%` }}
            />
          </div>
          {ladder.learnedSkills.length ? (
            <div>
              <p className="mb-1.5 text-xs font-semibold text-ink-muted">
                Habilidades que ya tienes
              </p>
              <ul className="flex flex-wrap gap-1.5">
                {ladder.learnedSkills.map((skill) => (
                  <li
                    key={skill.slug}
                    className="rounded-full bg-primary-soft px-2.5 py-1 text-xs font-medium text-primary"
                  >
                    {skill.name}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-ink-muted">
              Marca “{isDrink ? "Ya lo preparé" : "Ya lo cociné"}” en cada{" "}
              {isDrink ? "trago" : "platillo"} y aquí verás las habilidades que vas ganando. Tu
              progreso se guarda en este navegador.
            </p>
          )}
        </div>
      </section>

      <ol className="space-y-6">
        {path.stages.map((stage, index) => (
          <Stage
            key={stage.position}
            stage={stage}
            progress={ladder.stages[index]}
            previous={index > 0 ? path.stages[index - 1] : null}
            current={stage.position === ladder.currentStage}
            isDrink={isDrink}
          />
        ))}
      </ol>
    </div>
  );
}

function Stage({
  stage,
  progress,
  previous,
  current,
  isDrink,
}: {
  stage: PathStage;
  progress: StageProgress;
  previous: PathStage | null;
  current: boolean;
  isDrink: boolean;
}) {
  const noun = isDrink ? ["trago", "tragos"] : ["platillo", "platillos"];
  return (
    <li
      aria-current={current ? "step" : undefined}
      className={cn(
        "rounded-lg border bg-surface p-5",
        current ? "border-primary shadow-lift" : "border-line",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-bold",
              progress.unlocked ? "bg-primary text-primary-ink" : "bg-surface-muted text-ink-muted",
            )}
          >
            {progress.unlocked ? (
              stage.position
            ) : (
              <Lock aria-label="Bloqueada" className="size-4" />
            )}
          </span>
          <div>
            <h2 className="text-lg font-bold">
              Etapa {stage.position} · {stage.title}
            </h2>
            {stage.description ? (
              <p className="text-sm text-ink-muted">{stage.description}</p>
            ) : null}
          </div>
        </div>
        <p className="text-sm text-ink-muted">
          {progress.cooked} de {progress.total}
          {progress.unlocked && progress.remainingToUnlock > 0
            ? ` · ${pluralize(progress.remainingToUnlock, noun[0], noun[1])} más para avanzar`
            : ""}
        </p>
      </div>
      {!progress.unlocked && previous ? (
        <p className="mt-3 rounded-md bg-surface-muted px-3 py-2 text-xs text-ink-muted">
          Te sugerimos empezar por la etapa {previous.position}: con{" "}
          {pluralize(previous.dishes_to_unlock, noun[0], noun[1])} de allí, esta etapa se
          desbloquea. Puedes verla y cocinar de aquí cuando quieras.
        </p>
      ) : null}
      <ul className="mt-4 divide-y divide-line">
        {stage.dishes.map(({ recipe, skills }) => (
          <li
            key={recipe.id}
            className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center"
          >
            <Link
              href={recipeHref(recipe.slug)}
              className="group flex min-w-0 flex-1 items-start gap-4"
            >
              <RecipeArt
                slug={recipe.slug}
                title={recipe.title}
                recipeType={recipe.recipe_type}
                categories={recipe.categories}
                imageUrl={recipe.image_url}
                className="size-16 shrink-0 rounded-md"
                iconClassName="size-8"
              />
              <span className="min-w-0">
                <span className="block font-semibold group-hover:text-primary">{recipe.title}</span>
                <RecipeMeta recipe={recipe} className="mt-1" />
                {skills.length ? (
                  <span className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="text-ink-muted">Aprendes:</span>
                    {skills.map((skill) => (
                      <span
                        key={skill.slug}
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2 py-0.5",
                          skill.is_new
                            ? "bg-accent-soft font-semibold text-accent-ink"
                            : "bg-surface-muted text-ink-muted",
                        )}
                        title={
                          skill.is_new
                            ? "Habilidad nueva en este platillo"
                            : "Repasas esta habilidad"
                        }
                      >
                        {skill.is_new ? <Sparkles aria-hidden="true" className="size-3" /> : null}
                        {skill.name}
                      </span>
                    ))}
                  </span>
                ) : null}
              </span>
            </Link>
            <CookedToggle slug={recipe.slug} kind={recipe.recipe_type} />
          </li>
        ))}
      </ul>
    </li>
  );
}
