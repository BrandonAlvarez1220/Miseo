import type { ReactNode } from "react";

import { Brand } from "@/components/layout/brand";

/** Top bar: brand on small screens, `children` is the search, `actions` the account area. */
export function AppTopbar({ children, actions }: { children?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur-md">
      <div className="flex h-16 items-center gap-4 px-4 sm:px-6 lg:h-20 lg:px-8">
        <Brand compact className="lg:hidden" />
        <div className="flex min-w-0 flex-1 items-center justify-end gap-3 lg:justify-start">
          {children}
        </div>
        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>
    </header>
  );
}
