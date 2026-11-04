import { describe, expect, it } from "vitest";

import { formatQuantity, parseDecimal, scaleQuantity, toFraction } from "./quantity";

const unit = (code: string, name: string, plural_name: string) => ({ code, name, plural_name });

describe("scaleQuantity", () => {
  it("scales proportionally to servings", () => {
    expect(scaleQuantity(800, 4, 2)).toBe(400);
    expect(scaleQuantity(2, 4, 6)).toBe(3);
  });

  it("keeps unknown quantities unknown", () => {
    expect(scaleQuantity(null, 4, 8)).toBeNull();
  });
});

describe("toFraction", () => {
  it.each([
    [0.5, "½"],
    [1.5, "1½"],
    [0.33, "⅓"],
    [0.66, "⅔"],
    [2, "2"],
    [2.97, "3"],
    [0.24, "¼"],
  ])("%s -> %s", (value, expected) => {
    expect(toFraction(value)).toBe(expected);
  });
});

describe("formatQuantity", () => {
  it("uses fractions for spoon and cup units with plurals", () => {
    expect(formatQuantity(1.5, null, unit("cup", "taza", "tazas"))).toEqual({
      amount: "1½",
      unit: "tazas",
    });
    expect(formatQuantity(0.5, null, unit("tsp", "cucharadita", "cucharaditas"))).toEqual({
      amount: "½",
      unit: "cucharadita",
    });
  });

  it("rounds metric amounts sensibly", () => {
    expect(formatQuantity(833.33, null, unit("g", "gramo", "gramos")).amount).toBe("835");
    expect(formatQuantity(37.5, null, unit("ml", "mililitro", "mililitros")).amount).toBe("38");
    expect(formatQuantity(1.25, null, unit("l", "litro", "litros")).amount).toBe("1,3");
  });

  it("omits the unit name for pieces", () => {
    expect(formatQuantity(3, null, unit("piece", "pieza", "piezas"))).toEqual({
      amount: "3",
      unit: null,
    });
  });

  it("formats ranges", () => {
    expect(formatQuantity(2, 3, unit("clove", "diente", "dientes"))).toEqual({
      amount: "2–3",
      unit: "dientes",
    });
  });

  it("shows only the unit when there is no amount", () => {
    expect(formatQuantity(null, null, unit("to_taste", "al gusto", "al gusto"))).toEqual({
      amount: null,
      unit: "al gusto",
    });
  });
});

describe("parseDecimal", () => {
  it("parses API decimal strings", () => {
    expect(parseDecimal("800.000")).toBe(800);
    expect(parseDecimal(null)).toBeNull();
    expect(parseDecimal("abc")).toBeNull();
  });
});
