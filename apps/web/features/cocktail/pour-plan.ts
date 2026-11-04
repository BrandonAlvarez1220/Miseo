import { formatQuantity, parseDecimal } from "@/lib/quantity";
import type { DrinkDetails, RecipeIngredient } from "@/types/api";

/**
 * Turns a drink recipe into a "pour plan": the data-driven script the cocktail
 * animation plays. Pure and deterministic, so every cocktail (including future
 * community recipes) animates without hand-made assets.
 */

export type Technique = "shake" | "stir" | "build" | "muddle" | "blend" | "float";

export type GarnishKind = "citrus-wheel" | "orange-peel" | "mint" | "cherry" | "salt-rim";

export interface LiquidPour {
  kind: "liquid";
  name: string;
  /** Millilitres; for "top up" lines (no quantity) a default volume is used. */
  ml: number;
  /** Added after the ice, as the last pour (sodas and other carbonated mixers). */
  topUp: boolean;
  color: string;
  label: string;
}

export interface SolidAdd {
  kind: "solid";
  name: string;
  /** Muddled leaves, sugar cubes, ginger slices... */
  shape: "leaf" | "cube" | "slice";
  count: number;
  color: string;
  label: string;
}

export type PourStep = LiquidPour | SolidAdd;

export interface PourPlan {
  glass: string;
  technique: Technique;
  steps: PourStep[];
  /** Volume-weighted color of all liquids once mixed. */
  mixedColor: string;
  /** Opacity of the served drink (clear spirits are nearly transparent). */
  mixedOpacity: number;
  carbonated: boolean;
  ice: boolean;
  garnishes: GarnishKind[];
}

const TECHNIQUES: Record<string, Technique> = {
  batido: "shake",
  "dry-shake": "shake",
  mezclado: "stir",
  construido: "build",
  machacado: "muddle",
  licuado: "blend",
  flotado: "float",
};

/** Glasses that are served over ice. Stemmed glasses are served "up" (no ice). */
const ICED_GLASSES = new Set(["rocks", "highball", "collins", "taza-de-cobre", "tiki"]);

/** Default volume for a "top up" line (e.g. "agua con gas, para completar"). */
const TOP_UP_ML = 100;
const FALLBACK_COLOR = "#e8eef0";

function hexToRgb(hex: string): [number, number, number] {
  const value = Number.parseInt(hex.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function rgbToHex([r, g, b]: [number, number, number]): string {
  return `#${[r, g, b].map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")}`;
}

/** Perceived lightness 0..1 (used to make clear liquids translucent). */
export function lightness(hex: string): number {
  const [r, g, b] = hexToRgb(hex);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

/**
 * Clear liquids (gin, vodka, white rum, soda) are transparent, not white: they
 * dilute a color without whitening it. They get a lower weight when mixing so a
 * Negroni stays deep red instead of turning pink.
 */
const CLEAR_LIQUID_LIGHTNESS = 0.88;
const CLEAR_LIQUID_WEIGHT = 0.2;

export function mixColors(parts: { color: string; ml: number }[]): string {
  const weighted = parts.map((part) => ({
    color: part.color,
    weight: part.ml * (lightness(part.color) >= CLEAR_LIQUID_LIGHTNESS ? CLEAR_LIQUID_WEIGHT : 1),
  }));
  const total = weighted.reduce((sum, p) => sum + p.weight, 0);
  if (total <= 0) return FALLBACK_COLOR;
  const mixed = weighted.reduce<[number, number, number]>(
    (acc, part) => {
      const [r, g, b] = hexToRgb(part.color);
      const weight = part.weight / total;
      return [acc[0] + r * weight, acc[1] + g * weight, acc[2] + b * weight];
    },
    [0, 0, 0],
  );
  return rgbToHex(mixed);
}

/** Converts a recipe line to millilitres when its unit is a volume. */
export function toMillilitres(line: RecipeIngredient): number | null {
  const quantity = parseDecimal(line.quantity);
  const factor = parseDecimal(line.unit?.to_base_factor);
  if (quantity === null || !line.unit || line.unit.unit_type !== "volume" || factor === null) {
    return null;
  }
  return quantity * factor;
}

/** Units you pour (vs. add with a spoon or by dashes). */
const POURED_UNITS = new Set(["ml", "cl", "l", "oz"]);

/** Caption in the recipe's own units: "Vierte 60 ml de ron", "Añade 2 dashes de angostura". */
function describe(line: RecipeIngredient): string {
  const { amount, unit } = formatQuantity(
    parseDecimal(line.quantity),
    parseDecimal(line.quantity_max),
    line.unit,
  );
  const poured = line.unit !== null && POURED_UNITS.has(line.unit.code);
  const verb = poured ? "Vierte" : "Añade";
  const name = line.ingredient.name.toLowerCase();
  if (!amount) return `${verb} ${name}`;
  // Bar shorthand for metric pours ("60 ml"); spelled-out names otherwise.
  const unitText = poured ? line.unit?.code : unit;
  return unitText ? `${verb} ${amount} ${unitText} de ${name}` : `${verb} ${amount} de ${name}`;
}

function solidShape(unitCode: string | null): SolidAdd["shape"] | null {
  if (unitCode === "leaf" || unitCode === "sprig") return "leaf";
  if (unitCode === "slice") return "slice";
  if (unitCode === "piece") return "cube";
  return null;
}

/**
 * Garnish shown on the glass. Derived from the free-text garnish field, so it is
 * purely decorative: unknown garnishes are simply not drawn.
 */
export function garnishesFrom(text: string | null | undefined): GarnishKind[] {
  if (!text) return [];
  const value = text.toLowerCase();
  const found: GarnishKind[] = [];
  if (value.includes("sal")) found.push("salt-rim");
  if (/(lima|lim[oó]n)/.test(value)) found.push("citrus-wheel");
  if (value.includes("naranja")) found.push("orange-peel");
  if (value.includes("menta")) found.push("mint");
  if (value.includes("cereza")) found.push("cherry");
  return found;
}

export function buildPourPlan(
  drink: Pick<DrinkDetails, "glass" | "technique" | "garnish">,
  ingredients: RecipeIngredient[],
): PourPlan {
  const technique = TECHNIQUES[drink.technique?.slug ?? ""] ?? "build";
  const glass = drink.glass?.slug ?? "rocks";
  const steps: PourStep[] = [];

  for (const line of ingredients) {
    // Optional garnish-only lines (orange slice "para decorar", salt rim) are
    // shown as garnish, not poured into the drink.
    if (line.is_optional) continue;
    const color = line.ingredient.color ?? FALLBACK_COLOR;
    const ml = toMillilitres(line);
    if (ml !== null) {
      steps.push({
        kind: "liquid",
        name: line.ingredient.name,
        ml,
        // In built drinks, sodas go in last (over the ice) to keep their bubbles.
        topUp: line.ingredient.is_carbonated && technique === "build",
        color,
        label: describe(line),
      });
      continue;
    }
    const shape = solidShape(line.unit?.code ?? null);
    const count = parseDecimal(line.quantity);
    if (shape && count !== null) {
      steps.push({
        kind: "solid",
        name: line.ingredient.name,
        shape,
        count: Math.max(1, Math.min(8, Math.round(count))),
        color,
        label: describe(line),
      });
      continue;
    }
    if (line.quantity === null && line.unit === null) {
      steps.push({
        kind: "liquid",
        name: line.ingredient.name,
        ml: TOP_UP_ML,
        topUp: true,
        color,
        label: `Completa con ${line.ingredient.name.toLowerCase()}`,
      });
    }
  }

  // Muddled solids go first; top-ups go last, as at a real bar.
  const order = (step: PourStep) => (step.kind === "solid" ? 0 : step.topUp ? 2 : 1);
  steps.sort((a, b) => order(a) - order(b));

  for (const step of steps) {
    if (step.kind === "liquid" && step.topUp && !step.label.startsWith("Completa")) {
      step.label = step.label.replace(/^(Vierte|Añade)/, "Completa con");
    }
  }

  const liquids = steps.filter((s): s is LiquidPour => s.kind === "liquid");
  const mixedColor = mixColors(liquids);
  const carbonated = ingredients.some((l) => !l.is_optional && l.ingredient.is_carbonated);

  return {
    glass,
    technique,
    steps,
    mixedColor,
    // Very light mixes (white rum + lime) render translucent; darker ones denser.
    mixedOpacity: Math.min(0.92, Math.max(0.45, 1.25 - lightness(mixedColor))),
    carbonated,
    ice: ICED_GLASSES.has(glass),
    garnishes: garnishesFrom(drink.garnish),
  };
}

/** Human description of the technique for captions. */
export const TECHNIQUE_CAPTIONS: Record<Technique, string> = {
  shake: "Bate con energía con hielo",
  stir: "Remueve con hielo hasta enfriar",
  build: "Remueve suavemente",
  muddle: "Machaca con suavidad",
  blend: "Licúa con hielo",
  float: "Vierte despacio para crear capas",
};
