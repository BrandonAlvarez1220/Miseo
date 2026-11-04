import type { Metadata } from "next";
import { Suspense } from "react";

import { MixologyRegion } from "@/components/layout/theme-region";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
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
        description="Aprende técnicas, cristalería y guarniciones. Distinguimos siempre entre clásicos documentados, variaciones y propuestas experimentales."
      />
      <Container className="space-y-6">
        <SectionHeading
          id="drink-categories"
          title="Categorías"
          description="Cócteles por estilo"
        />
        <Suspense fallback={<CategoryGridSkeleton />}>
          <CategorySection recipeType="drink" retryHref={MODULES.drink.href} />
        </Suspense>
      </Container>
    </MixologyRegion>
  );
}
