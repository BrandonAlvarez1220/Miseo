import { describe, expect, it } from "vitest";

import type { RecipeIngredient } from "@/types/api";

import { buildPourPlan, garnishesFrom, mixColors, toMillilitres } from "./pour-plan";

const ml = {
  code: "ml",
  name: "mililitro",
  plural_name: "mililitros",
  unit_type: "volume" as const,
  to_base_factor: "1.000000",
};
const dash = {
  code: "dash",
  name: "dash",
  plural_name: "dashes",
  unit_type: "volume" as const,
  to_base_factor: "0.900000",
};
const leaf = {
  code: "leaf",
  name: "hoja",
  plural_name: "hojas",
  unit_type: "count" as const,
  to_base_factor: null,
};
const slice = {
  code: "slice",
  name: "rodaja",
  plural_name: "rodajas",
  unit_type: "count" as const,
  to_base_factor: null,
};

function line(
  name: string,
  overrides: Partial<RecipeIngredient> = {},
  color = "#ffffff",
): RecipeIngredient {
  return {
    ingredient: { id: name, slug: name, name, color, is_carbonated: false },
    quantity: null,
    quantity_max: null,
    unit: null,
    is_optional: false,
    preparation_notes: null,
    group_label: null,
    alternatives: [],
    ...overrides,
  };
}

const drink = (glass: string, technique: string, garnish: string | null = null) => ({
  glass: { slug: glass, name: glass, description: null },
  technique: { slug: technique, name: technique, description: null },
  garnish,
});

describe("toMillilitres", () => {
  it("converts volume units and ignores counts", () => {
    expect(toMillilitres(line("ron", { quantity: "60.000", unit: ml }))).toBe(60);
    expect(toMillilitres(line("angostura", { quantity: "2.000", unit: dash }))).toBeCloseTo(1.8);
    expect(toMillilitres(line("menta", { quantity: "6.000", unit: leaf }))).toBeNull();
  });
});

describe("mixColors", () => {
  it("weights colors by volume", () => {
    expect(
      mixColors([
        { color: "#ff0000", ml: 30 },
        { color: "#0000ff", ml: 30 },
      ]),
    ).toBe("#800080");
    expect(
      mixColors([
        { color: "#808080", ml: 90 },
        { color: "#000000", ml: 10 },
      ]),
    ).toBe("#737373");
  });

  it("lets clear liquids dilute without whitening", () => {
    // 30 ml gin + 30 ml Campari: the clear part weighs 0.2, so the mix stays red
    // (a plain average would give a washed-out pink).
    const mixed = mixColors([
      { color: "#eef2f3", ml: 30 },
      { color: "#c8102e", ml: 30 },
    ]);
    const [r, g, b] = [1, 3, 5].map((i) => Number.parseInt(mixed.slice(i, i + 2), 16));
    expect(r).toBeGreaterThan(190);
    expect(g).toBeLessThan(70);
    expect(b).toBeLessThan(90);
  });
});

describe("buildPourPlan", () => {
  const mojito = [
    line("Ron blanco", { quantity: "45.000", unit: ml }, "#f3efe4"),
    line("Agua con gas", {}, "#e6f2f7"),
    line("Menta", { quantity: "6.000", unit: leaf }, "#3c9a48"),
    line("Lima", { quantity: "20.000", unit: ml }, "#cfe39a"),
  ];
  mojito[1].ingredient.is_carbonated = true;

  it("orders solids first and top-ups last, with captions", () => {
    const plan = buildPourPlan(
      drink("highball", "machacado", "Ramita de menta y rueda de lima"),
      mojito,
    );

    expect(plan.steps.map((s) => s.label)).toEqual([
      "Añade 6 hojas de menta",
      "Vierte 45 ml de ron blanco",
      "Vierte 20 ml de lima",
      "Completa con agua con gas",
    ]);
    expect(plan.technique).toBe("muddle");
    expect(plan.carbonated).toBe(true);
    expect(plan.ice).toBe(true);
    expect(plan.garnishes).toEqual(["citrus-wheel", "mint"]);
  });

  it("serves stemmed glasses without ice and skips optional garnish lines", () => {
    const negroniLike = [
      line("Ginebra", { quantity: "30.000", unit: ml }, "#eef2f3"),
      line("Naranja", { quantity: "0.500", unit: slice, is_optional: true }, "#f59e3c"),
    ];
    const plan = buildPourPlan(drink("coupe", "batido"), negroniLike);

    expect(plan.ice).toBe(false);
    expect(plan.technique).toBe("shake");
    expect(plan.steps).toHaveLength(1);
  });

  it("falls back to build in a rocks glass when data is missing", () => {
    const plan = buildPourPlan({ glass: null, technique: null, garnish: null }, [
      line("X", { quantity: "10.000", unit: ml }),
    ]);
    expect(plan.glass).toBe("rocks");
    expect(plan.technique).toBe("build");
  });

  it("renders light mixes translucent and dark ones dense", () => {
    const light = buildPourPlan(drink("coupe", "batido"), [
      line("ron", { quantity: "60.000", unit: ml }, "#f3efe4"),
    ]);
    const dark = buildPourPlan(drink("highball", "construido"), [
      line("cola", { quantity: "120.000", unit: ml }, "#3a1d10"),
    ]);
    expect(light.mixedOpacity).toBeLessThan(dark.mixedOpacity);
  });
});

describe("captions", () => {
  const tsp = {
    code: "tsp",
    name: "cucharadita",
    plural_name: "cucharaditas",
    unit_type: "volume" as const,
    to_base_factor: "5.000000",
  };

  it("uses the recipe's own units and the right verb", () => {
    const plan = buildPourPlan(drink("rocks", "construido"), [
      line("Azúcar", { quantity: "2.000", unit: tsp }),
      line("Angostura", { quantity: "2.000", unit: dash }),
    ]);
    expect(plan.steps.map((s) => s.label)).toEqual([
      "Añade 2 cucharaditas de azúcar",
      "Añade 2 dashes de angostura",
    ]);
  });

  it("puts measured sodas last in built drinks", () => {
    const cola = line("Cola", { quantity: "120.000", unit: ml }, "#3a1d10");
    cola.ingredient.is_carbonated = true;
    const plan = buildPourPlan(drink("highball", "construido"), [
      line("Ron blanco", { quantity: "50.000", unit: ml }),
      cola,
      line("Lima", { quantity: "10.000", unit: ml }),
    ]);
    expect(plan.steps.map((s) => s.label)).toEqual([
      "Vierte 50 ml de ron blanco",
      "Vierte 10 ml de lima",
      "Completa con 120 ml de cola",
    ]);
  });
});

describe("garnishesFrom", () => {
  it("recognizes common garnishes and ignores the rest", () => {
    expect(garnishesFrom("Media corona de sal y rueda de lima")).toEqual([
      "salt-rim",
      "citrus-wheel",
    ]);
    expect(garnishesFrom("Piel de naranja y cereza")).toEqual(["orange-peel", "cherry"]);
    expect(garnishesFrom("Flor comestible")).toEqual([]);
    expect(garnishesFrom(null)).toEqual([]);
  });
});
