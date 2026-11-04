import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
import { MODULES } from "@/lib/modules";

export const metadata: Metadata = {
  title: "Cocina",
  description: "Recetas de cocina abiertas: explora por categoría, tiempo y dificultad.",
};

export default function KitchenPage() {
  return (
    <>
      <PageHeader
        lead="Recetas para cocinar"
        title="con lo que tienes a mano"
        description="Platos caseros, clásicos de siempre y propuestas de la comunidad, con ingredientes, cantidades y pasos claros."
      />
      <Container className="space-y-6">
        <SectionHeading
          id="kitchen-categories"
          title="Categorías"
          description="Recetas por tipo de plato"
        />
        <Suspense fallback={<CategoryGridSkeleton />}>
          <CategorySection recipeType="cooking" retryHref={MODULES.cooking.href} />
        </Suspense>
      </Container>
    </>
  );
}
