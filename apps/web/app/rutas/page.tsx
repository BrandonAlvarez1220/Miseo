import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { PathCards } from "@/features/paths/path-cards";

export const metadata: Metadata = {
  title: "Rutas de aprendizaje",
  description:
    "Aprende cocinando: una escalera de platillos de fáciles a complejos, y otra de tragos para la barra.",
};

export default function PathsPage() {
  return (
    <>
      <PageHeader
        lead="Aprende cocinando,"
        title="un platillo a la vez"
        description="Cada ruta es una escalera de platillos reales, de lo más sencillo a lo más elaborado. Las habilidades —tiempos de cocción, sellar, batir— se aprenden por el camino."
      />
      <Container>
        <Suspense
          fallback={
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-64 rounded-lg" />
              <Skeleton className="h-64 rounded-lg" />
            </div>
          }
        >
          <PathCards retryHref="/rutas" />
        </Suspense>
      </Container>
    </>
  );
}
