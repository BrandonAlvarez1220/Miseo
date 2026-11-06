import { describe, expect, it } from "vitest";

import { parseRecipeSearchParams, recipesHref } from "./search-params";

describe("parseRecipeSearchParams", () => {
  it("parses valid params", () => {
    expect(
      parseRecipeSearchParams({ q: " pollo ", tipo: "cooking", tiempo: "30", pagina: "2" }),
    ).toMatchObject({ q: "pollo", tipo: "cooking", tiempo: 30, pagina: 2 });
  });

  it("drops invalid values instead of failing", () => {
    const parsed = parseRecipeSearchParams({ tipo: "pizza", tiempo: "-5", pagina: "abc" });
    expect(parsed.tipo).toBeUndefined();
    expect(parsed.tiempo).toBeUndefined();
    expect(parsed.pagina).toBe(1);
  });
});

describe("recipesHref", () => {
  it("skips empty values and the first page", () => {
    expect(recipesHref({ q: "sopa", tipo: undefined, pagina: 1 })).toBe("/recetas?q=sopa");
    expect(recipesHref({})).toBe("/recetas");
    expect(recipesHref({ categoria: "sours", pagina: 3 })).toBe(
      "/recetas?categoria=sours&pagina=3",
    );
  });
});
