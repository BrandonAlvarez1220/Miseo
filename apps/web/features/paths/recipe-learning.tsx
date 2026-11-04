import { GraduationCap, Lightbulb } from "lucide-react";
import Link from "next/link";

import type { RecipeDetail } from "@/types/api";

import { CookedToggle } from "./cooked-toggle";

/** "Lo que aprendes" block on a recipe page, with its place in the learning paths. */
export function RecipeLearning({ recipe }: { recipe: RecipeDetail }) {
  if (recipe.skills.length === 0 && recipe.paths.length === 0) return null;
  return (
    <section aria-labelledby="learning" className="rounded-lg border border-line bg-surface p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 id="learning" className="flex items-center gap-2 text-xl font-bold">
          <GraduationCap aria-hidden="true" className="size-5 text-primary" />
          Lo que aprendes
        </h2>
        <CookedToggle slug={recipe.slug} kind={recipe.recipe_type} size="md" />
      </div>
      {recipe.skills.length ? (
        <ul className="space-y-2">
          {recipe.skills.map((skill) => (
            <li key={skill.slug}>
              <details className="group rounded-md bg-surface-muted px-4 py-3">
                <summary className="cursor-pointer list-none font-medium marker:hidden">
                  <span className="flex items-center justify-between gap-2">
                    {skill.name}
                    <Lightbulb aria-hidden="true" className="size-4 text-notice" />
                  </span>
                </summary>
                <p className="mt-2 text-sm text-ink-muted">{skill.tip}</p>
              </details>
            </li>
          ))}
        </ul>
      ) : null}
      {recipe.paths.map((membership) => (
        <p key={membership.path_slug} className="mt-4 text-sm text-ink-muted">
          Forma parte de la etapa {membership.stage_position} ({membership.stage_title}) de{" "}
          <Link
            href={`/rutas/${membership.path_slug}`}
            className="font-semibold text-primary hover:underline"
          >
            {membership.path_title}
          </Link>
          .
        </p>
      ))}
    </section>
  );
}
