import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * Renders its children with the Mixology (night) tokens. Applied per page or
 * section instead of from the URL, so dynamic routes (e.g. a drink's detail
 * page) can opt in based on their data.
 */
export function MixologyRegion({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div data-theme="mixology" className={cn("bg-canvas text-ink", className)} {...props} />;
}
