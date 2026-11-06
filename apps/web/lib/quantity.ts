import type { DecimalString, Unit } from "@/types/api";

/** Units measured with spoons/cups or counted pieces read better as fractions. */
const FRACTION_UNITS = new Set([
  "tsp",
  "tbsp",
  "cup",
  "bar_spoon",
  "piece",
  "slice",
  "clove",
  "leaf",
  "sprig",
  "pinch",
  "dash",
  "drop",
  "oz",
  "oz_wt",
  "lb",
]);

const FRACTIONS: [number, string][] = [
  [0, ""],
  [1 / 4, "¼"],
  [1 / 3, "⅓"],
  [1 / 2, "½"],
  [2 / 3, "⅔"],
  [3 / 4, "¾"],
  [1, ""],
];

export function parseDecimal(value: DecimalString | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Proportional scaling for a different number of servings. */
export function scaleQuantity(
  quantity: number | null,
  baseServings: number,
  servings: number,
): number | null {
  if (quantity === null || baseServings <= 0) return quantity;
  return (quantity * servings) / baseServings;
}

/** 1.5 -> "1½", 0.333 -> "⅓", 2 -> "2". Rounds to the nearest common fraction. */
export function toFraction(value: number): string {
  const whole = Math.floor(value);
  const remainder = value - whole;
  let best = FRACTIONS[0];
  for (const candidate of FRACTIONS) {
    if (Math.abs(candidate[0] - remainder) < Math.abs(best[0] - remainder)) best = candidate;
  }
  const [fraction, glyph] = best;
  if (fraction === 1) return String(whole + 1);
  if (whole === 0) return glyph || "0";
  return `${whole}${glyph}`;
}

/** Metric amounts: whole numbers, rounded to 5 above 100 (e.g. 833 g -> 835 g). */
function formatMetric(value: number): string {
  if (value >= 100) return String(Math.round(value / 5) * 5);
  if (value >= 10) return String(Math.round(value));
  return String(Math.round(value * 10) / 10).replace(".", ",");
}

export function formatNumber(value: number, unitCode: string | null): string {
  if (unitCode === null || FRACTION_UNITS.has(unitCode)) return toFraction(value);
  return formatMetric(value);
}

export interface QuantityParts {
  amount: string | null;
  unit: string | null;
}

/**
 * Human readable quantity for an ingredient line, already scaled.
 * Units without a number ("al gusto") are returned as the unit text only.
 */
export function formatQuantity(
  quantity: number | null,
  quantityMax: number | null,
  unit: Pick<Unit, "code" | "name" | "plural_name"> | null,
): QuantityParts {
  if (quantity === null) {
    return { amount: null, unit: unit ? unit.name : null };
  }
  const code = unit?.code ?? null;
  const amount =
    quantityMax !== null && quantityMax !== quantity
      ? `${formatNumber(quantity, code)}–${formatNumber(quantityMax, code)}`
      : formatNumber(quantity, code);
  if (!unit || unit.code === "piece") return { amount, unit: null };
  const plural = (quantityMax ?? quantity) > 1;
  return { amount, unit: plural ? unit.plural_name : unit.name };
}
