import type { SubmissionDetail } from "@/types/api";

import type { ApprovePayload } from "./api";

/** What the reviewer decided for a line the catalog could not match. */
export type LineChoice =
  | { mode: "unset" }
  | { mode: "map"; slug: string }
  | { mode: "create"; name: string; category: string | null };

export interface ReviewDecisions {
  lineChoices: Record<number, LineChoice>;
  unitChoices: Record<number, string>;
  categories: string[];
  skills: string[];
  /** "path_slug:stage_position" or "" for none. */
  placement: string;
  classification: string;
  notes: string;
}

/** Lines that still need a decision: no catalog ingredient and no choice yet. */
export function unresolvedLines(
  detail: Pick<SubmissionDetail, "lines">,
  choices: Record<number, LineChoice>,
): number[] {
  return detail.lines
    .filter((line) => {
      if (line.ingredient_slug) return false;
      const choice = choices[line.index];
      if (!choice || choice.mode === "unset") return true;
      if (choice.mode === "map") return choice.slug.trim() === "";
      return choice.name.trim() === "";
    })
    .map((line) => line.index);
}

/** Lines with a unit the catalog does not know and no unit chosen yet. */
export function unresolvedUnits(
  detail: Pick<SubmissionDetail, "lines">,
  unitChoices: Record<number, string>,
): number[] {
  return detail.lines
    .filter((line) => line.unit_text && !line.unit_code && !unitChoices[line.index])
    .map((line) => line.index);
}

/** Request body for the approve endpoint. Only sends what the reviewer actually decided. */
export function buildApprovePayload(
  detail: Pick<SubmissionDetail, "lines" | "recipe_type">,
  decisions: ReviewDecisions,
): ApprovePayload {
  const ingredient_mappings: ApprovePayload["ingredient_mappings"] = {};
  const new_ingredients: ApprovePayload["new_ingredients"] = {};
  for (const [index, choice] of Object.entries(decisions.lineChoices)) {
    if (choice.mode === "map" && choice.slug.trim()) {
      ingredient_mappings[index] = choice.slug.trim();
    } else if (choice.mode === "create" && choice.name.trim()) {
      new_ingredients[index] = { name: choice.name.trim(), category: choice.category || null };
    }
  }
  const unit_mappings: ApprovePayload["unit_mappings"] = {};
  for (const [index, code] of Object.entries(decisions.unitChoices)) {
    if (code) unit_mappings[index] = code;
  }

  const [pathSlug, stage] = decisions.placement.split(":");
  const payload: ApprovePayload = {
    ingredient_mappings,
    new_ingredients,
    unit_mappings,
    categories: decisions.categories,
    skills: decisions.skills,
    placement: pathSlug && stage ? { path_slug: pathSlug, stage_position: Number(stage) } : null,
    review_notes: decisions.notes.trim() || null,
  };
  if (detail.recipe_type === "drink" && decisions.classification) {
    payload.classification = decisions.classification;
  }
  return payload;
}
