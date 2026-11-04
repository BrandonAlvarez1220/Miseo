import { GitFork } from "lucide-react";
import { Suspense } from "react";

import { Brand } from "@/components/layout/brand";
import { NavList, NavListFallback } from "@/components/layout/nav-list";
import { REPOSITORY_URL } from "@/lib/site";

export function AppSidebar() {
  return (
    // The outer column stretches with the page (background and border); the inner
    // panel stays pinned to the viewport.
    <div className="hidden w-64 shrink-0 border-r border-line bg-surface lg:block">
      <aside className="sticky top-0 flex h-dvh flex-col">
        <div className="flex h-20 items-center border-b border-line px-6">
          <Brand />
        </div>
        <nav aria-label="Principal" className="flex-1 overflow-y-auto px-4 py-6">
          <p className="mb-3 px-3 text-[11px] font-semibold tracking-[0.14em] text-ink-muted uppercase">
            Menú
          </p>
          <Suspense fallback={<NavListFallback variant="sidebar" />}>
            <NavList variant="sidebar" />
          </Suspense>
        </nav>
        <div className="relative m-4 overflow-hidden rounded-lg bg-accent p-5 text-white">
          <div
            aria-hidden="true"
            className="absolute -top-10 -right-10 size-32 rounded-full bg-white/10"
          />
          <p className="relative text-base leading-snug font-bold">Miseo es open source</p>
          <p className="relative mt-1 text-sm text-white/90">
            Recetas, código e ideas hechas por la comunidad.
          </p>
          <a
            href={REPOSITORY_URL}
            target="_blank"
            rel="noreferrer"
            className="relative mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-full bg-white text-sm font-semibold text-ink transition-colors hover:bg-white/90"
          >
            <GitFork aria-hidden="true" className="size-4" /> Contribuir en GitHub
          </a>
        </div>
      </aside>
    </div>
  );
}
