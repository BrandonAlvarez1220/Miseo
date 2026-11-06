import type { RecipeType } from "@/types/api";

/** The two product modules. Route paths are user-facing, hence in Spanish. */
export const MODULES = {
  cooking: { recipeType: "cooking", href: "/cocina", label: "Cocina" },
  drink: { recipeType: "drink", href: "/mixologia", label: "Mixología" },
} as const satisfies Record<RecipeType, { recipeType: RecipeType; href: string; label: string }>;
