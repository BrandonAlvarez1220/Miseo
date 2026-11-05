import { CheckCircle2, XCircle } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";

import { apiErrorState } from "@/components/ui/api-error-state";
import { Container } from "@/components/ui/container";
import { Skeleton } from "@/components/ui/skeleton";
import { Forbidden } from "@/features/auth/forbidden";
import { requireRole } from "@/features/auth/guard";
import { getSubmission, loadReviewCatalogs } from "@/features/review/api";
import { ReviewPanel } from "@/features/review/review-panel";
import { StatusBadge } from "@/features/review/status-badge";
import { SubmissionSummary } from "@/features/review/submission-summary";
import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";

export const metadata: Metadata = { title: "Revisar receta" };

export default function SubmissionPage({ params }: PageProps<"/revision/[id]">) {
  return (
    <Container className="space-y-6 py-8">
      <Link href="/revision" className="text-sm font-medium text-ink-muted hover:text-ink">
        ← Volver a la cola
      </Link>
      <Suspense fallback={<Skeleton className="h-96 w-full rounded-lg" />}>
        <Detail params={params} />
      </Suspense>
    </Container>
  );
}

async function Detail({ params }: Pick<PageProps<"/revision/[id]">, "params">) {
  await connection();
  const { id } = await params;
  const session = await requireRole("moderator", `/revision/${id}`);
  if (!session) return <Forbidden needs="moderadores y administradores" />;

  const result = await attempt(getSubmission(session.token, id));
  if (!result.ok) {
    if (
      result.error instanceof ApiError &&
      (result.error.status === 404 || result.error.status === 422)
    ) {
      notFound();
    }
    return apiErrorState(result.error, `/revision/${id}`, "el envío");
  }
  const detail = result.data;
  const pending = detail.status === "needs_review";
  const catalogs = pending ? await attempt(loadReviewCatalogs(detail.recipe_type)) : null;
  if (catalogs && !catalogs.ok)
    return apiErrorState(catalogs.error, `/revision/${id}`, "los catálogos");

  return (
    <>
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-balance">{detail.title}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            {detail.recipe_type === "drink" ? "Bebida" : "Receta de cocina"} · enviada el{" "}
            {new Date(detail.created_at).toLocaleString("es", {
              dateStyle: "long",
              timeStyle: "short",
            })}
          </p>
        </div>
        <StatusBadge status={detail.status} />
      </header>

      {detail.status === "completed" ? (
        <p className="flex items-start gap-2 rounded-md bg-primary-soft px-4 py-3 text-sm text-primary">
          <CheckCircle2 aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          <span>
            Publicada.{" "}
            {detail.recipe_slug ? (
              <Link href={`/recetas/${detail.recipe_slug}`} className="font-semibold underline">
                Ver la receta
              </Link>
            ) : null}
            {detail.review_notes ? ` Notas: ${detail.review_notes}` : ""}
          </span>
        </p>
      ) : null}
      {detail.status === "rejected" ? (
        <p className="flex items-start gap-2 rounded-md bg-surface-muted px-4 py-3 text-sm">
          <XCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-ink-muted" />
          <span>
            <span className="font-semibold">Rechazada.</span> Motivo: {detail.review_notes}
          </span>
        </p>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] xl:items-start">
        <SubmissionSummary detail={detail} />
        {catalogs?.ok ? (
          <div className="xl:sticky xl:top-24">
            <ReviewPanel
              detail={detail}
              units={catalogs.data.units}
              ingredientCategories={catalogs.data.ingredientCategories}
              categories={catalogs.data.categories}
            />
          </div>
        ) : null}
      </div>
    </>
  );
}
