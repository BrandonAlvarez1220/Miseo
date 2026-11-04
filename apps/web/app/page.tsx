import { ArrowRight, ChefHat, Martini } from "lucide-react";
import Link from "next/link";
import { Suspense, type ReactNode } from "react";

import { buttonVariants } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Container } from "@/components/ui/container";
import { SectionHeading } from "@/components/ui/section-heading";
import { CategoryGridSkeleton } from "@/features/categories/category-grid-skeleton";
import { CategorySection } from "@/features/categories/category-section";
import { MODULES } from "@/lib/modules";
import { cn } from "@/lib/utils";

export default function HomePage() {
  return (
    <>
      <section className="pt-14 pb-16 sm:pt-24 sm:pb-24">
        <Container>
          <Chip tone="primary" size="sm" className="mb-6">
            Open source · Hecho por la comunidad
          </Chip>
          <h1 className="max-w-4xl font-display text-5xl leading-[1.02] font-semibold tracking-tight text-balance sm:text-7xl">
            Descubre lo que puedes crear con lo que ya tienes.
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-ink-muted text-pretty sm:text-xl">
            Recetas de cocina y cócteles con ingredientes estructurados, cantidades claras y
            fuentes siempre atribuidas. Gratis, abierto y sin depender de la IA.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href={MODULES.cooking.href} className={buttonVariants({ size: "lg" })}>
              <ChefHat aria-hidden="true" /> Explorar cocina
            </Link>
            <Link
              href={MODULES.drink.href}
              className={buttonVariants({ variant: "secondary", size: "lg" })}
            >
              <Martini aria-hidden="true" /> Explorar mixología
            </Link>
          </div>
        </Container>
      </section>

      <Container className="space-y-20">
        <div className="grid gap-4 md:grid-cols-2">
          <ModulePanel
            href={MODULES.cooking.href}
            icon={<ChefHat aria-hidden="true" className="size-6" />}
            title="Cocina"
            description="Desayunos, guisos, pastas, postres y todo lo que cabe en tu cocina."
          />
          <ModulePanel
            mixology
            href={MODULES.drink.href}
            icon={<Martini aria-hidden="true" className="size-6" />}
            title="Mixología"
            description="Clásicos documentados, variaciones, técnicas de barra y mocktails."
          />
        </div>

        <section aria-labelledby="home-kitchen-categories" className="space-y-6">
          <SectionHeading
            id="home-kitchen-categories"
            eyebrow="Cocina"
            title="Explora por categoría"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="cooking" retryHref="/" />
          </Suspense>
        </section>

        <section
          data-theme="mixology"
          aria-labelledby="home-drink-categories"
          className="-mx-4 space-y-6 rounded-none bg-canvas px-4 py-12 text-ink sm:mx-0 sm:rounded-xl sm:px-10"
        >
          <SectionHeading
            id="home-drink-categories"
            eyebrow="Mixología"
            title="Para la hora del cóctel"
          />
          <Suspense fallback={<CategoryGridSkeleton />}>
            <CategorySection recipeType="drink" retryHref="/" />
          </Suspense>
        </section>
      </Container>
    </>
  );
}

interface ModulePanelProps {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
  mixology?: boolean;
}

function ModulePanel({ href, icon, title, description, mixology = false }: ModulePanelProps) {
  return (
    <Link
      href={href}
      data-theme={mixology ? "mixology" : undefined}
      className={cn(
        "group flex min-h-56 flex-col justify-between rounded-xl p-7 shadow-soft transition-shadow hover:shadow-lift sm:p-9",
        mixology ? "bg-canvas text-ink" : "bg-primary-soft text-ink",
      )}
    >
      <span className="inline-flex size-12 items-center justify-center rounded-full bg-surface text-primary">
        {icon}
      </span>
      <span>
        <span className="flex items-center gap-2 font-display text-3xl font-semibold">
          {title}
          <ArrowRight
            aria-hidden="true"
            className="size-6 transition-transform group-hover:translate-x-1"
          />
        </span>
        <span className="mt-2 block text-ink-muted">{description}</span>
      </span>
    </Link>
  );
}
