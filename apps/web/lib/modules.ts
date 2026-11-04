import type { RecipeType } from "@/types/api";

/** The two product modules. Route paths are user-facing, hence in Spanish. */
export const MODULES = {
  cooking: {
    recipeType: "cooking",
    href: "/cocina",
    label: "Cocina",
    theme: "kitchen",
  },
  drink: {
    recipeType: "drink",
    href: "/mixologia",
    label: "Mixología",
    theme: "mixology",
  },
} as const satisfies Record<
  RecipeType,
  { recipeType: RecipeType; href: string; label: string; theme: "kitchen" | "mixology" }
>;

export type Theme = (typeof MODULES)[RecipeType]["theme"];

export function themeForPath(pathname: string): Theme {
  const isMixology =
    pathname === MODULES.drink.href || pathname.startsWith(`${MODULES.drink.href}/`);
  return isMixology ? "mixology" : "kitchen";
}
