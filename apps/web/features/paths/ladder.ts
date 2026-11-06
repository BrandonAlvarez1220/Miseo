import type { PathDetail, Skill } from "@/types/api";

export interface StageProgress {
  position: number;
  cooked: number;
  total: number;
  /** Suggested gate: previous stage reached its `dishes_to_unlock`. Never blocks browsing. */
  unlocked: boolean;
  /** Dishes still needed in this stage to unlock the next one. */
  remainingToUnlock: number;
}

export interface LadderProgress {
  stages: StageProgress[];
  /** Highest unlocked stage: where the user should cook next. */
  currentStage: number;
  cookedDishes: number;
  totalDishes: number;
  /** Skills learned from the dishes already cooked, in ladder order. */
  learnedSkills: Skill[];
}

export function computeLadder(path: PathDetail, cooked: ReadonlySet<string>): LadderProgress {
  const stages: StageProgress[] = [];
  let unlocked = true;
  for (const stage of path.stages) {
    const cookedHere = stage.dishes.filter((d) => cooked.has(d.recipe.slug)).length;
    stages.push({
      position: stage.position,
      cooked: cookedHere,
      total: stage.dishes.length,
      unlocked,
      remainingToUnlock: Math.max(0, stage.dishes_to_unlock - cookedHere),
    });
    unlocked = unlocked && cookedHere >= stage.dishes_to_unlock;
  }

  const learned = new Map<string, Skill>();
  for (const stage of path.stages) {
    for (const dish of stage.dishes) {
      if (!cooked.has(dish.recipe.slug)) continue;
      for (const skill of dish.skills) {
        if (!learned.has(skill.slug)) learned.set(skill.slug, skill);
      }
    }
  }

  const unlockedStages = stages.filter((s) => s.unlocked);
  return {
    stages,
    currentStage: unlockedStages.at(-1)?.position ?? 1,
    cookedDishes: stages.reduce((sum, s) => sum + s.cooked, 0),
    totalDishes: stages.reduce((sum, s) => sum + s.total, 0),
    learnedSkills: [...learned.values()],
  };
}
