import { Martini } from "lucide-react";
import type { Metadata } from "next";
import { Suspense } from "react";

import { ModuleHero } from "@/components/modules/module-hero";
import { Container } from "@/components/ui/container";
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
    <>
      <ModuleHero
        icon={Martini}
        eyebrow="Mixología"
        title="Cócteles clásicos, variaciones y bebidas sin alcohol."
        description="Aprende técnicas, cristalería y guarniciones. Distinguimos siempre entre clásicos documentados, variaciones y propuestas experimentales."
      />
      <Container>
        <section aria-labelledby="drink-categories" className="space-y-6">
          <SectionHeading id="drink-categories" title="Categorías" />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="drink" retryHref={MODULES.drink.href} />
          </Suspense>
        </section>
      </Container>
    </>
  );
}
