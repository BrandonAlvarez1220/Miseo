import { Suspense } from "react";

import { NavList, NavListFallback } from "@/components/layout/nav-list";

export function MobileTabBar() {
  return (
    <nav
      aria-label="Principal (móvil)"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden"
    >
      <Suspense fallback={<NavListFallback variant="tabbar" />}>
        <NavList variant="tabbar" />
      </Suspense>
    </nav>
  );
}
