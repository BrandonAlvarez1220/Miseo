import { ArrowUpRight, ChefHat, Martini } from "lucide-react";
import Link from "next/link";
import { Suspense, type ReactNode } from "react";

import { MixologyRegion } from "@/components/layout/theme-region";
import { Container } from "@/components/ui/container";
import { PageHeader } from "@/components/ui/page-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
import { MODULES } from "@/lib/modules";

export default function HomePage() {
  return (
    <>
      <PageHeader
        lead="Recetas desde tu"
        title="propia cocina"
        description="Descubre lo que puedes crear con lo que ya tienes: recetas y cócteles con ingredientes estructurados y fuentes siempre atribuidas."
      />
      <Container className="space-y-12">
        <div className="grid gap-4 md:grid-cols-2">
          <ModuleCard
            href={MODULES.cooking.href}
            icon={<ChefHat aria-hidden="true" className="size-6" />}
            title="Cocina"
            description="Desayunos, guisos, pastas, postres y todo lo que cabe en tu cocina."
          />
          <MixologyRegion className="rounded-lg">
            <ModuleCard
              href={MODULES.drink.href}
              icon={<Martini aria-hidden="true" className="size-6" />}
              title="Mixología"
              description="Clásicos documentados, variaciones, técnicas de barra y mocktails."
            />
          </MixologyRegion>
        </div>

        <section aria-labelledby="home-kitchen-categories" className="space-y-5">
          <SectionHeading
            id="home-kitchen-categories"
            title="Cocina por categorías"
            description="Recetas agrupadas por tipo de plato"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="cooking" retryHref="/" />
          </Suspense>
        </section>

        <section aria-labelledby="home-drink-categories" className="space-y-5">
          <SectionHeading
            id="home-drink-categories"
            title="Mixología por categorías"
            description="Cócteles y bebidas sin alcohol por estilo"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="drink" retryHref="/" />
          </Suspense>
        </section>
      </Container>
    </>
  );
}

interface ModuleCardProps {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
}

function ModuleCard({ href, icon, title, description }: ModuleCardProps) {
  return (
    <Link
      href={href}
      className="group flex h-full items-start gap-4 rounded-lg border border-line bg-surface p-6 transition-shadow hover:shadow-lift"
    >
      <span className="inline-flex size-12 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
        {icon}
      </span>
      <span className="flex-1">
        <span className="block text-lg font-bold">{title}</span>
        <span className="mt-1 block text-sm text-ink-muted">{description}</span>
      </span>
      <ArrowUpRight
        aria-hidden="true"
        className="size-5 text-ink-muted transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
      />
    </Link>
  );
}
