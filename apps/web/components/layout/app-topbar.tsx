import type { ReactNode } from "react";

import { Brand } from "@/components/layout/brand";

/** Top bar: brand on small screens; `children` holds global actions (search). */
export function AppTopbar({ children }: { children?: ReactNode }) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur-md">
      <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:h-20 lg:px-8">
        <Brand compact className="lg:hidden" />
        <div className="flex flex-1 items-center justify-end gap-3 lg:justify-start">
          {children}
        </div>
      </div>
    </header>
  );
}
