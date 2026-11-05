import { describe, expect, it } from "vitest";

import { describeDetails } from "./describe-details";

describe("describeDetails", () => {
  it("turns unresolved lines into readable sentences, 1-based", () => {
    expect(
      describeDetails([
        { line: 4, problem: "ingredient", name: "chorizo" },
        { line: 0, problem: "unit", text: "puñado" },
      ]),
    ).toEqual([
      "Línea 5: falta resolver el ingrediente «chorizo».",
      "Línea 1: falta resolver la unidad «puñado».",
    ]);
  });

  it("keeps plain messages and ignores anything else", () => {
    expect(describeDetails([{ message: "algo falló" }, "texto", null, 3])).toEqual(["algo falló"]);
    expect(describeDetails(undefined)).toEqual([]);
  });
});
