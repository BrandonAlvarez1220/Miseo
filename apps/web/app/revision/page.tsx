import { Inbox } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Pagination } from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { StateMessage } from "@/components/ui/state-message";
import { Forbidden } from "@/features/auth/forbidden";
import { requireRole } from "@/features/auth/guard";
import { listSubmissions } from "@/features/review/api";
import { StatusBadge } from "@/features/review/status-badge";
import { attempt } from "@/lib/attempt";
import { DIFFICULTY_LABELS, pluralize } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { IngestionStatus } from "@/types/api";

export const metadata: Metadata = { title: "Revisión de recetas" };

const TABS: { key: string; label: string; status: IngestionStatus }[] = [
  { key: "pendientes", label: "Por revisar", status: "needs_review" },
  { key: "aprobadas", label: "Publicadas", status: "completed" },
  { key: "rechazadas", label: "Rechazadas", status: "rejected" },
];

export default function ReviewQueuePage({ searchParams }: PageProps<"/revision">) {
  return (
    <>
      <PageHeader
        lead="Recetas enviadas"
        title="por los agentes"
        description="Nada se publica sin que una persona lo apruebe. Revisa la fuente, resuelve los ingredientes que el catálogo no reconoce y decide."
      />
      <Container className="space-y-6">
        <Suspense fallback={<Skeleton className="h-64 w-full rounded-lg" />}>
          <Queue searchParams={searchParams} />
        </Suspense>
      </Container>
    </>
  );
}

async function Queue({ searchParams }: Pick<PageProps<"/revision">, "searchParams">) {
  await connection();
  const params = await searchParams;
  const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);
  const tab = TABS.find((t) => t.key === first(params.estado)) ?? TABS[0];
  const page = Math.max(1, Number.parseInt(first(params.pagina) ?? "1", 10) || 1);

  const session = await requireRole("moderator", `/revision?estado=${tab.key}`);
  if (!session) return <Forbidden needs="moderadores y administradores" />;

  const result = await attempt(listSubmissions(session.token, { status: tab.status, page }));
  if (!result.ok) return apiErrorState(result.error, `/revision?estado=${tab.key}`, "la cola");
  const { items, total, pages } = result.data;

  return (
    <>
      <nav aria-label="Estado" className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Link
            key={t.key}
            href={`/revision?estado=${t.key}`}
            aria-current={t.key === tab.key ? "page" : undefined}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
              t.key === tab.key
                ? "bg-primary text-primary-ink"
                : "border border-line hover:bg-surface-muted",
            )}
          >
            {t.label}
          </Link>
        ))}
      </nav>

      {items.length === 0 ? (
        <StateMessage
          icon={Inbox}
          title={tab.status === "needs_review" ? "No hay nada pendiente" : "Aún no hay nada aquí"}
          description={
            tab.status === "needs_review"
              ? "Cuando un agente envíe una receta aparecerá aquí."
              : "Las decisiones que tomes aparecerán en esta lista."
          }
        />
      ) : (
        <>
          <p className="text-sm text-ink-muted" aria-live="polite">
            {pluralize(total, "receta", "recetas")}
          </p>
          <ul className="space-y-3">
            {items.map((item) => (
              <li key={item.id}>
                <Link
                  href={`/revision/${item.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface p-4 transition-shadow hover:shadow-lift"
                >
                  <span className="min-w-0">
                    <span className="block font-bold">{item.title}</span>
                    <span className="mt-1 block text-xs text-ink-muted">
                      {item.recipe_type === "drink" ? "Bebida" : "Cocina"}
                      {item.agent ? ` · ${item.agent.name}` : ""}
                      {item.difficulty_score
                        ? ` · dificultad ${item.difficulty_score}/5 (${DIFFICULTY_LABELS[item.difficulty_score <= 2 ? "easy" : item.difficulty_score === 3 ? "medium" : "hard"]})`
                        : ""}
                      {" · "}
                      {new Date(item.created_at).toLocaleString("es", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </span>
                  </span>
                  <span className="flex items-center gap-2 text-xs">
                    {item.errors ? (
                      <span className="rounded-full bg-danger-soft px-2.5 py-1 font-semibold text-danger">
                        {pluralize(item.errors, "error", "errores")}
                      </span>
                    ) : null}
                    {item.warnings ? (
                      <span className="rounded-full bg-notice-soft px-2.5 py-1 font-semibold text-notice">
                        {pluralize(item.warnings, "aviso", "avisos")}
                      </span>
                    ) : null}
                    <StatusBadge status={item.status} />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
          <Pagination
            page={page}
            pages={pages}
            hrefFor={(n) => `/revision?estado=${tab.key}&pagina=${n}`}
          />
        </>
      )}
    </>
  );
}
