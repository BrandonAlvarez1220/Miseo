import { ShieldCheck } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";

import { MixologyRegion } from "@/components/layout/theme-region";
import { apiErrorState } from "@/components/ui/api-error-state";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { getPath } from "@/features/paths/api";
import { PathLadder } from "@/features/paths/path-ladder";
import { ApiError } from "@/lib/api-client";
import { attempt } from "@/lib/attempt";

export async function generateMetadata({ params }: PageProps<"/rutas/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const result = await attempt(getPath(slug));
  return result.ok
    ? { title: result.data.title, description: result.data.description ?? undefined }
    : { title: "Ruta de aprendizaje" };
}

export default function PathPage({ params }: PageProps<"/rutas/[slug]">) {
  return (
    <Suspense fallback={<LadderSkeleton />}>
      <PathView params={params} />
    </Suspense>
  );
}

async function PathView({ params }: Pick<PageProps<"/rutas/[slug]">, "params">) {
  await connection();
  const { slug } = await params;
  const result = await attempt(getPath(slug));
  if (!result.ok) {
    if (result.error instanceof ApiError && result.error.status === 404) notFound();
    return (
      <Container className="py-10">
        {apiErrorState(result.error, `/rutas/${slug}`, "la ruta")}
      </Container>
    );
  }
  const path = result.data;
  const isDrink = path.discipline === "drink";
  const content = (
    <>
      <PageHeader
        lead={isDrink ? "Ruta de barra:" : "Ruta de cocina:"}
        title={path.title}
        description={path.description}
      >
        <Link
          href="/rutas"
          className="mt-4 inline-block text-sm font-medium text-ink-muted hover:text-ink"
        >
          ← Todas las rutas
        </Link>
      </PageHeader>
      <Container className="space-y-6">
        {isDrink ? (
          <p className="flex items-start gap-2 rounded-md bg-notice-soft px-4 py-3 text-sm">
            <ShieldCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-notice" />
            Contenido para mayores de edad. Bebe con moderación: cada etapa incluye opciones sin
            alcohol cuando existen.
          </p>
        ) : null}
        <PathLadder path={path} />
      </Container>
    </>
  );
  return isDrink ? (
    <MixologyRegion className="min-h-full pb-12">{content}</MixologyRegion>
  ) : (
    content
  );
}

function LadderSkeleton() {
  return (
    <Container className="space-y-6 pt-10">
      <Skeleton className="h-24 w-2/3" />
      <Skeleton className="h-32 w-full rounded-lg" />
      <Skeleton className="h-72 w-full rounded-lg" />
    </Container>
  );
}
