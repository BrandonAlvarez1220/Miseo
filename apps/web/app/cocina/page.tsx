import { ChefHat } from "lucide-react";
import type { Metadata } from "next";
import { Suspense } from "react";

import { ModuleHero } from "@/components/modules/module-hero";
import { Container } from "@/components/ui/container";
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
      <ModuleHero
        icon={ChefHat}
        eyebrow="Cocina"
        title="Recetas para cocinar con lo que tienes a mano."
        description="Platos caseros, clásicos de siempre y propuestas de la comunidad, con ingredientes, cantidades y pasos claros."
      />
      <Container>
        <section aria-labelledby="kitchen-categories" className="space-y-6">
          <SectionHeading id="kitchen-categories" title="Categorías" />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="cooking" retryHref={MODULES.cooking.href} />
          </Suspense>
        </section>
      </Container>
    </>
  );
}
