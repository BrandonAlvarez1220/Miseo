import { describe, expect, it } from "vitest";

import { pantryHref, parsePantryParams } from "./search-params";

describe("parsePantryParams", () => {
  it("parses ingredients, mode, type and staples", () => {
    expect(
      parsePantryParams({ i: "pollo,arroz,pollo", modo: "exact", tipo: "cooking", basicos: "0" }),
    ).toEqual({
      ingredients: ["pollo", "arroz"],
      mode: "exact",
      recipeType: "cooking",
      assumeStaples: false,
    });
  });

  it("falls back to safe defaults for invalid values", () => {
    expect(parsePantryParams({ i: "Pollo!,ok", modo: "magic", tipo: "x" })).toEqual({
      ingredients: ["ok"],
      mode: "flexible",
      recipeType: null,
      assumeStaples: true,
    });
  });
});

describe("pantryHref", () => {
  it("omits defaults and keeps commas readable", () => {
    expect(
      pantryHref({
        ingredients: ["pollo", "arroz"],
        mode: "flexible",
        recipeType: null,
        assumeStaples: true,
      }),
    ).toBe("/que-puedo-preparar?i=pollo,arroz");
  });

  it("round-trips through the parser", () => {
    const params = {
      ingredients: ["lima", "ron-blanco"],
      mode: "discover" as const,
      recipeType: "drink" as const,
      assumeStaples: false,
    };
    const url = new URL(pantryHref(params), "http://x");
    expect(parsePantryParams(url.searchParams)).toEqual(params);
  });
});
