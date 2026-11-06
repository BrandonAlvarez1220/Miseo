import { describe, expect, it } from "vitest";

import type { PathDetail, RecipeSummary } from "@/types/api";

import { computeLadder } from "./ladder";

const recipe = (slug: string) => ({ slug, title: slug }) as RecipeSummary;
const skill = (slug: string, is_new = true) => ({ slug, name: slug, tip: "", is_new });

const path: PathDetail = {
  slug: "cocina",
  title: "Cocina",
  discipline: "cooking",
  description: null,
  stage_count: 3,
  dish_count: 5,
  skill_count: 3,
  stages: [
    {
      position: 1,
      title: "Fácil",
      description: null,
      dishes_to_unlock: 2,
      dishes: [
        { recipe: recipe("huevos"), skills: [skill("picar")] },
        { recipe: recipe("sopa"), skills: [skill("caldillo")] },
        { recipe: recipe("quesadillas"), skills: [] },
      ],
    },
    {
      position: 2,
      title: "Casa",
      description: null,
      dishes_to_unlock: 1,
      dishes: [{ recipe: recipe("bistec"), skills: [skill("picar", false), skill("sellar")] }],
    },
    {
      position: 3,
      title: "Retos",
      description: null,
      dishes_to_unlock: 1,
      dishes: [{ recipe: recipe("pozole"), skills: [] }],
    },
  ],
};

describe("computeLadder", () => {
  it("starts at the first stage with nothing cooked", () => {
    const ladder = computeLadder(path, new Set());

    expect(ladder.currentStage).toBe(1);
    expect(ladder.stages.map((s) => s.unlocked)).toEqual([true, false, false]);
    expect(ladder.stages[0].remainingToUnlock).toBe(2);
    expect(ladder.learnedSkills).toEqual([]);
  });

  it("unlocks the next stage after enough dishes, without requiring all of them", () => {
    const ladder = computeLadder(path, new Set(["huevos", "sopa"]));

    expect(ladder.stages.map((s) => s.unlocked)).toEqual([true, true, false]);
    expect(ladder.currentStage).toBe(2);
    expect(ladder.cookedDishes).toBe(2);
    expect(ladder.totalDishes).toBe(5);
  });

  it("does not skip stages: cooking a later dish does not unlock past a gate", () => {
    const ladder = computeLadder(path, new Set(["bistec"]));

    expect(ladder.stages.map((s) => s.unlocked)).toEqual([true, false, false]);
    expect(ladder.stages[1].cooked).toBe(1);
  });

  it("collects learned skills without duplicates, in ladder order", () => {
    const ladder = computeLadder(path, new Set(["huevos", "bistec"]));
    expect(ladder.learnedSkills.map((s) => s.slug)).toEqual(["picar", "sellar"]);
  });
});
