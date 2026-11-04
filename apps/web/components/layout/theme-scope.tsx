"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { themeForPath } from "@/lib/modules";

/**
 * Switches the color tokens for the whole page depending on the module:
 * Mixology routes render with the night palette.
 */
export function ThemeScope({ children }: { children: ReactNode }) {
  const theme = themeForPath(usePathname());
  return (
    <div
      data-theme={theme === "mixology" ? "mixology" : undefined}
      className="flex min-h-full flex-1 flex-col bg-canvas text-ink transition-colors duration-300"
    >
      {children}
    </div>
  );
}
