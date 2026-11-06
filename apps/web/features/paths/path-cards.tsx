import { ArrowRight, ChefHat, Martini } from "lucide-react";
import Link from "next/link";
import { connection } from "next/server";

import { MixologyRegion } from "@/components/layout/theme-region";
import { apiErrorState } from "@/components/ui/api-error-state";
import { StateMessage } from "@/components/ui/state-message";
import { attempt } from "@/lib/attempt";
import { pluralize } from "@/lib/format";
import type { PathSummary } from "@/types/api";

import { listPaths } from "./api";

/** Cards for every learning path. Render inside <Suspense>. */
export async function PathCards({ retryHref }: { retryHref: string }) {
  await connection();
  const result = await attempt(listPaths());
  if (!result.ok) return apiErrorState(result.error, retryHref, "las rutas");
  if (result.data.length === 0) {
    return <StateMessage icon={ChefHat} title="Todavía no hay rutas publicadas" />;
  }
  return (
    <ul className="grid gap-4 md:grid-cols-2">
      {result.data.map((path) => (
        <li key={path.slug}>
          {path.discipline === "drink" ? (
            <MixologyRegion className="h-full rounded-lg">
              <PathCard path={path} />
            </MixologyRegion>
          ) : (
            <PathCard path={path} />
          )}
        </li>
      ))}
    </ul>
  );
}

function PathCard({ path }: { path: PathSummary }) {
  const Icon = path.discipline === "drink" ? Martini : ChefHat;
  const noun = path.discipline === "drink" ? ["trago", "tragos"] : ["platillo", "platillos"];
  return (
    <Link
      href={`/rutas/${path.slug}`}
      className="group flex h-full flex-col rounded-lg border border-line bg-surface p-6 transition-shadow hover:shadow-lift"
    >
      <span className="inline-flex size-12 items-center justify-center rounded-full bg-primary-soft text-primary">
        <Icon aria-hidden="true" className="size-6" />
      </span>
      <span className="mt-4 text-xs font-semibold tracking-[0.14em] text-ink-muted uppercase">
        {path.discipline === "drink" ? "Ruta de barra" : "Ruta de cocina"}
      </span>
      <span className="mt-1 text-xl font-bold group-hover:text-primary">{path.title}</span>
      {path.description ? (
        <span className="mt-2 text-sm text-ink-muted">{path.description}</span>
      ) : null}
      <span className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-5 text-sm">
        <span className="text-ink-muted">
          {pluralize(path.stage_count, "etapa", "etapas")} ·{" "}
          {pluralize(path.dish_count, noun[0], noun[1])} ·{" "}
          {pluralize(path.skill_count, "habilidad", "habilidades")}
        </span>
        <span className="inline-flex items-center gap-1 font-semibold text-primary">
          Empezar <ArrowRight aria-hidden="true" className="size-4" />
        </span>
      </span>
    </Link>
  );
}
