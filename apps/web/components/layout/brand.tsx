import { CookingPot } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

export function Brand({ compact = false, className }: { compact?: boolean; className?: string }) {
  return (
    <Link href="/" className={cn("flex items-center gap-3", className)} aria-label="Miseo, inicio">
      <span className="inline-flex size-10 items-center justify-center rounded-full bg-accent-soft text-accent">
        <CookingPot aria-hidden="true" className="size-5" />
      </span>
      <span className="leading-tight">
        <span className="block text-lg font-bold tracking-tight">
          Mis<span className="text-accent">eo</span>
        </span>
        {compact ? null : <span className="block text-xs text-ink-muted">Cocina y mixología</span>}
      </span>
    </Link>
  );
}
