import { Refrigerator } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { buttonVariants } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
import { LatestRecipes } from "@/features/recipes/latest-recipes";
import { RecipeGridSkeleton } from "@/features/recipes/recipe-grid";
import { recipesHref } from "@/features/recipes/search-params";
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
        actions={
          <Link href="/que-puedo-preparar?tipo=cooking" className={buttonVariants({ size: "lg" })}>
            <Refrigerator aria-hidden="true" /> Cocinar con lo que tengo
          </Link>
        }
      />
      <Container className="space-y-14">
        <section aria-labelledby="kitchen-categories" className="space-y-5">
          <SectionHeading
            id="kitchen-categories"
            title="Categorías"
            description="Recetas por tipo de plato"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="cooking" retryHref={MODULES.cooking.href} />
          </Suspense>
        </section>
        <section aria-labelledby="kitchen-latest" className="space-y-5">
          <SectionHeading
            id="kitchen-latest"
            title="Últimas recetas"
            action={
              <Link
                href={recipesHref({ tipo: "cooking" })}
                className={buttonVariants({ variant: "outline", size: "pill" })}
              >
                Ver todas
              </Link>
            }
          />
          <Suspense fallback={<RecipeGridSkeleton />}>
            <LatestRecipes recipeType="cooking" retryHref={MODULES.cooking.href} />
          </Suspense>
        </section>
      </Container>
    </>
  );
}
