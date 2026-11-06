"use client";

import { Check, CookingPot } from "lucide-react";

import { cn } from "@/lib/utils";

import { setCooked, useCookedRecipes } from "./progress";

interface CookedToggleProps {
  slug: string;
  /** "drink" changes the wording ("Ya lo preparé"). */
  kind?: "cooking" | "drink";
  size?: "sm" | "md";
}

export function CookedToggle({ slug, kind = "cooking", size = "sm" }: CookedToggleProps) {
  const cooked = useCookedRecipes().has(slug);
  const label = kind === "drink" ? "Ya lo preparé" : "Ya lo cociné";
  return (
    <button
      type="button"
      aria-pressed={cooked}
      onClick={() => setCooked(slug, !cooked)}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border font-semibold transition-colors [&_svg]:size-4",
        size === "sm" ? "h-8 px-3 text-xs" : "h-11 px-5 text-sm",
        cooked
          ? "border-primary bg-primary text-primary-ink"
          : "border-line text-ink-muted hover:border-primary hover:text-primary",
      )}
    >
      {cooked ? <Check aria-hidden="true" /> : <CookingPot aria-hidden="true" />}
      {label}
    </button>
  );
}
