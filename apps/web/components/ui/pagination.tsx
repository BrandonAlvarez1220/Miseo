import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  pages: number;
  hrefFor: (page: number) => string;
}

export function Pagination({ page, pages, hrefFor }: PaginationProps) {
  if (pages <= 1) return null;
  const linkClass = buttonVariants({ variant: "secondary", size: "sm" });
  return (
    <nav aria-label="Paginación" className="flex items-center justify-center gap-3">
      {page > 1 ? (
        <Link href={hrefFor(page - 1)} className={linkClass} rel="prev">
          <ChevronLeft aria-hidden="true" /> Anterior
        </Link>
      ) : null}
      <p className="text-sm text-ink-muted">
        Página <span className="font-semibold text-ink">{page}</span> de {pages}
      </p>
      {page < pages ? (
        <Link href={hrefFor(page + 1)} className={cn(linkClass)} rel="next">
          Siguiente <ChevronRight aria-hidden="true" />
        </Link>
      ) : null}
    </nav>
  );
}
