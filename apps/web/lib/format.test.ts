import { describe, expect, it } from "vitest";

import { capitalizeFirst, formatMinutes, pluralize } from "./format";

describe("capitalizeFirst", () => {
  it("capitalizes only the first letter, including accented ones", () => {
    expect(capitalizeFirst("chile guajillo")).toBe("Chile guajillo");
    expect(capitalizeFirst("  ñame morado ")).toBe("Ñame morado");
    expect(capitalizeFirst("ya Está")).toBe("Ya Está");
    expect(capitalizeFirst("")).toBe("");
  });
});

describe("formatMinutes / pluralize", () => {
  it("formats durations and counts", () => {
    expect(formatMinutes(45)).toBe("45 min");
    expect(formatMinutes(75)).toBe("1 h 15 min");
    expect(formatMinutes(null)).toBeNull();
    expect(pluralize(1, "receta", "recetas")).toBe("1 receta");
    expect(pluralize(2, "receta", "recetas")).toBe("2 recetas");
  });
});
