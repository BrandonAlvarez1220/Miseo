import {
  CakeSlice,
  ChefHat,
  Citrus,
  CupSoda,
  Drumstick,
  EggFried,
  Fish,
  GlassWater,
  HandPlatter,
  Leaf,
  Martini,
  Salad,
  Soup,
  TreePalm,
  Wheat,
  Wine,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { CategoryRef, RecipeType } from "@/types/api";

/**
 * Visual stand-in until recipes have real photography: an icon chosen from the
 * recipe's first category on a tinted background derived from its slug, so the
 * same recipe always looks the same.
 */
const CATEGORY_ICONS: Record<string, LucideIcon> = {
  desayunos: EggFried,
  entradas: HandPlatter,
  "sopas-y-cremas": Soup,
  ensaladas: Salad,
  "pastas-y-arroces": Wheat,
  "carnes-y-aves": Drumstick,
  "pescados-y-mariscos": Fish,
  vegetariano: Leaf,
  postres: CakeSlice,
  clasicos: Martini,
  sours: Citrus,
  highballs: CupSoda,
  tropicales: TreePalm,
  aperitivos: Wine,
  "sin-alcohol": GlassWater,
  // Fallbacks when no category has a dedicated icon.
  "fallback-cooking": ChefHat,
  "fallback-drink": Martini,
};

const TINTS = [
  "bg-[#fde8dc] text-[#c4501f]",
  "bg-[#e3f2e8] text-[#1c7a45]",
  "bg-[#fdf1d6] text-[#a8700f]",
  "bg-[#e6eefb] text-[#3c62b0]",
  "bg-[#f6e6f0] text-[#a33f78]",
  "bg-[#eaf3dc] text-[#5b7d1c]",
];

const DRINK_TINTS = [
  "bg-[#2a2433] text-[#f0a93b]",
  "bg-[#1f2b33] text-[#7cc4d8]",
  "bg-[#33222b] text-[#ec6d93]",
  "bg-[#25301f] text-[#a7d36b]",
];

function hash(value: string): number {
  let h = 0;
  for (const char of value) h = (h * 31 + char.charCodeAt(0)) >>> 0;
  return h;
}

interface RecipeArtProps {
  slug: string;
  title: string;
  recipeType: RecipeType;
  categories: CategoryRef[];
  imageUrl?: string | null;
  className?: string;
  iconClassName?: string;
}

export function RecipeArt({
  slug,
  title,
  recipeType,
  categories,
  imageUrl,
  className,
  iconClassName,
}: RecipeArtProps) {
  if (imageUrl) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- remote hosts are not configured yet
      <img src={imageUrl} alt={title} className={cn("object-cover", className)} loading="lazy" />
    );
  }
  const palette = recipeType === "drink" ? DRINK_TINTS : TINTS;
  const iconKey =
    categories.map((c) => c.slug).find((slug) => slug in CATEGORY_ICONS) ??
    `fallback-${recipeType}`;
  const Icon = CATEGORY_ICONS[iconKey];
  return (
    <div
      aria-hidden="true"
      className={cn(
        "flex items-center justify-center",
        palette[hash(slug) % palette.length],
        className,
      )}
    >
      <Icon className={cn("size-10", iconClassName)} strokeWidth={1.5} />
    </div>
  );
}
