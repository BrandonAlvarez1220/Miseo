import { describe, expect, it } from "vitest";

import type { SubmissionLine } from "@/types/api";

import {
  buildApprovePayload,
  unresolvedLines,
  unresolvedUnits,
  type ReviewDecisions,
} from "./approve-payload";

const line = (index: number, overrides: Partial<SubmissionLine> = {}): SubmissionLine => ({
  index,
  name: `linea ${index}`,
  ingredient_slug: "huevo",
  ingredient_name: "Huevo",
  candidates: [],
  quantity: null,
  quantity_max: null,
  unit_code: "g",
  unit_text: "g",
  optional: false,
  notes: null,
  group: null,
  ...overrides,
});

const decisions = (overrides: Partial<ReviewDecisions> = {}): ReviewDecisions => ({
  lineChoices: {},
  unitChoices: {},
  categories: ["desayunos"],
  skills: ["cuajar-huevo"],
  placement: "",
  classification: "",
  notes: "",
  ...overrides,
});

describe("unresolvedLines", () => {
  const detail = {
    lines: [line(0), line(1, { ingredient_slug: null }), line(2, { ingredient_slug: null })],
  };

  it("lists the lines without a catalog ingredient and without a decision", () => {
    expect(unresolvedLines(detail, {})).toEqual([1, 2]);
  });

  it("counts a mapping or a creation as resolved, but not an empty one", () => {
    expect(
      unresolvedLines(detail, {
        1: { mode: "map", slug: "pollo" },
        2: { mode: "create", name: "  ", category: null },
      }),
    ).toEqual([2]);
    expect(
      unresolvedLines(detail, {
        1: { mode: "map", slug: "" },
        2: { mode: "create", name: "Chile guajillo", category: null },
      }),
    ).toEqual([1]);
  });
});

describe("unresolvedUnits", () => {
  it("flags only units written by the agent that the catalog does not know", () => {
    const detail = {
      lines: [
        line(0),
        line(1, { unit_code: null, unit_text: "puñado" }),
        line(2, { unit_code: null, unit_text: null }),
      ],
    };
    expect(unresolvedUnits(detail, {})).toEqual([1]);
    expect(unresolvedUnits(detail, { 1: "piece" })).toEqual([]);
  });
});

describe("buildApprovePayload", () => {
  const detail = { lines: [line(0)], recipe_type: "cooking" as const };

  it("sends only the decisions made, trimmed", () => {
    const payload = buildApprovePayload(
      detail,
      decisions({
        lineChoices: {
          1: { mode: "map", slug: " pollo " },
          2: { mode: "create", name: " Chile guajillo ", category: "especias" },
          3: { mode: "unset" },
        },
        unitChoices: { 4: "piece", 5: "" },
        notes: "  ok  ",
        placement: "cocina:2",
      }),
    );

    expect(payload).toEqual({
      ingredient_mappings: { "1": "pollo" },
      new_ingredients: { "2": { name: "Chile guajillo", category: "especias" } },
      unit_mappings: { "4": "piece" },
      categories: ["desayunos"],
      skills: ["cuajar-huevo"],
      placement: { path_slug: "cocina", stage_position: 2 },
      review_notes: "ok",
    });
  });

  it("omits placement and notes when empty, and classification for cooking recipes", () => {
    const payload = buildApprovePayload(detail, decisions({ classification: "classic" }));
    expect(payload.placement).toBeNull();
    expect(payload.review_notes).toBeNull();
    expect(payload).not.toHaveProperty("classification");
  });

  it("sends the classification for drinks", () => {
    const payload = buildApprovePayload(
      { lines: [], recipe_type: "drink" },
      decisions({ classification: "contemporary" }),
    );
    expect(payload.classification).toBe("contemporary");
  });
});
