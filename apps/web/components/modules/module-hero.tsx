import type { LucideIcon } from "lucide-react";

import { Container } from "@/components/ui/container";

interface ModuleHeroProps {
  icon: LucideIcon;
  eyebrow: string;
  title: string;
  description: string;
}

export function ModuleHero({ icon: Icon, eyebrow, title, description }: ModuleHeroProps) {
  return (
    <section className="pt-12 pb-10 sm:pt-20 sm:pb-14">
      <Container>
        <div className="mb-6 inline-flex size-12 items-center justify-center rounded-full bg-primary-soft text-primary">
          <Icon aria-hidden="true" className="size-6" />
        </div>
        <p className="mb-3 text-xs font-semibold tracking-[0.18em] text-primary uppercase">{eyebrow}</p>
        <h1 className="max-w-3xl font-display text-4xl leading-[1.05] font-semibold tracking-tight text-balance sm:text-6xl">
          {title}
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-ink-muted text-pretty">{description}</p>
      </Container>
    </section>
  );
}
