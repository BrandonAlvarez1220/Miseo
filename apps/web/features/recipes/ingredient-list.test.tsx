import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { RecipeIngredient } from "@/types/api";

import { IngredientList } from "./ingredient-list";

const unit = (code: string, name: string, plural_name: string) => ({
  code,
  name,
  plural_name,
  unit_type: "mass" as const,
  to_base_factor: null,
});

const line = (overrides: Partial<RecipeIngredient>): RecipeIngredient => ({
  ingredient: { id: "x", slug: "x", name: "X", color: null, is_carbonated: false },
  quantity: null,
  quantity_max: null,
  unit: null,
  is_optional: false,
  preparation_notes: null,
  group_label: null,
  alternatives: [],
  ...overrides,
});

const ingredients = [
  line({
    ingredient: { id: "1", slug: "arroz", name: "Arroz", color: null, is_carbonated: false },
    quantity: "2.000",
    unit: unit("cup", "taza", "tazas"),
  }),
  line({
    ingredient: { id: "2", slug: "sal", name: "Sal", color: null, is_carbonated: false },
    unit: unit("to_taste", "al gusto", "al gusto"),
  }),
  line({
    ingredient: { id: "3", slug: "lima", name: "Lima", color: null, is_carbonated: false },
    quantity: "1.000",
    is_optional: true,
    alternatives: [
      {
        ingredient: { id: "4", slug: "limon", name: "Limón" },
        substitution_type: "similar",
        ratio: "1.000",
        notes: null,
      },
    ],
  }),
];

describe("IngredientList", () => {
  it("scales quantities with the servings stepper and can reset", async () => {
    const user = userEvent.setup();
    render(<IngredientList ingredients={ingredients} baseServings={4} servingLabel="Porciones" />);
    const rows = () => screen.getAllByRole("listitem");

    expect(rows()[0]).toHaveTextContent("2 tazasArroz");
    await user.click(screen.getByRole("button", { name: "Menos porciones" }));
    await user.click(screen.getByRole("button", { name: "Menos porciones" }));
    expect(rows()[0]).toHaveTextContent("1 tazaArroz");
    await user.click(screen.getByRole("button", { name: "Menos porciones" }));
    expect(rows()[0]).toHaveTextContent("½ tazaArroz");

    await user.click(screen.getByRole("button", { name: "Restablecer" }));
    expect(rows()[0]).toHaveTextContent("2 tazas");
  });

  it("shows unit-only lines, optional badges and substitutions", () => {
    render(<IngredientList ingredients={ingredients} baseServings={4} servingLabel="Porciones" />);
    const [, salt, lime] = screen.getAllByRole("listitem");

    expect(salt).toHaveTextContent("al gustoSal");
    expect(within(lime).getByText("opcional")).toBeInTheDocument();
    expect(lime).toHaveTextContent("Sustituye por Limón (similar)");
  });

  it("never goes below one serving", () => {
    render(<IngredientList ingredients={ingredients} baseServings={1} servingLabel="Bebidas" />);
    expect(screen.getByRole("button", { name: "Menos porciones" })).toBeDisabled();
  });
});
