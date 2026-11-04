import { Martini } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { MixologyRegion } from "@/components/layout/theme-region";
import { buttonVariants } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { Skeleton } from "@/components/ui/skeleton";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
import { BarGuide } from "@/features/mixology/bar-guide";
import { LatestRecipes } from "@/features/recipes/latest-recipes";
import { RecipeGridSkeleton } from "@/features/recipes/recipe-grid";
import { recipesHref } from "@/features/recipes/search-params";
import { MODULES } from "@/lib/modules";

export const metadata: Metadata = {
  title: "Mixología",
  description: "Cócteles clásicos, variaciones documentadas y bebidas sin alcohol.",
};

export default function MixologyPage() {
  return (
    <MixologyRegion className="min-h-full pb-12">
      <PageHeader
        lead="Cócteles clásicos,"
        title="variaciones y sin alcohol"
        description="Distinguimos siempre entre clásicos documentados, variaciones y propuestas contemporáneas o experimentales."
        actions={
          <Link href="/que-puedo-preparar?tipo=drink" className={buttonVariants({ size: "lg" })}>
            <Martini aria-hidden="true" /> Qué cóctel puedo hacer
          </Link>
        }
      />
      <Container className="space-y-14">
        <section aria-labelledby="drink-categories" className="space-y-5">
          <SectionHeading
            id="drink-categories"
            title="Categorías"
            description="Cócteles por estilo"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="drink" retryHref={MODULES.drink.href} />
          </Suspense>
        </section>
        <section aria-labelledby="drink-latest" className="space-y-5">
          <SectionHeading
            id="drink-latest"
            title="Cócteles y bebidas"
            action={
              <Link
                href={recipesHref({ tipo: "drink" })}
                className={buttonVariants({ variant: "outline", size: "pill" })}
              >
                Ver todos
              </Link>
            }
          />
          <Suspense fallback={<RecipeGridSkeleton />}>
            <LatestRecipes recipeType="drink" retryHref={MODULES.drink.href} />
          </Suspense>
        </section>
        <section aria-labelledby="bar-guide" className="space-y-5">
          <SectionHeading
            id="bar-guide"
            title="Guía de barra"
            description="Técnicas y cristalería que aparecen en las recetas"
          />
          <Suspense fallback={<Skeleton className="h-80 w-full rounded-lg" />}>
            <BarGuide />
          </Suspense>
        </section>
      </Container>
    </MixologyRegion>
  );
}
