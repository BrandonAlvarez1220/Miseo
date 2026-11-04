import Link from "next/link";

import { NavLink } from "@/components/layout/nav-link";
import { Container } from "@/components/ui/container";
import { MODULES } from "@/lib/modules";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line/60 bg-canvas/85 backdrop-blur-md">
      <Container className="flex h-16 items-center justify-between gap-4">
        <Link href="/" className="font-display text-2xl font-semibold tracking-tight">
          Miseo<span className="text-primary">.</span>
        </Link>
        <nav aria-label="Principal" className="flex items-center gap-1">
          <NavLink href={MODULES.cooking.href}>{MODULES.cooking.label}</NavLink>
          <NavLink href={MODULES.drink.href}>{MODULES.drink.label}</NavLink>
        </nav>
      </Container>
    </header>
  );
}
