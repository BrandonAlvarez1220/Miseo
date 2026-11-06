import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PathDetail, RecipeSummary } from "@/types/api";

import { PathLadder } from "./path-ladder";
import { resetProgressCache } from "./progress";

const recipe = (slug: string, title: string): RecipeSummary => ({
  id: slug,
  slug,
  title,
  description: null,
  image_url: null,
  recipe_type: "cooking",
  difficulty: "easy",
  servings: 2,
  preparation_time_minutes: 10,
  cooking_time_minutes: 10,
  total_time_minutes: 20,
  categories: [],
  ingredient_count: 3,
  is_alcoholic: null,
  published_at: null,
});

const path: PathDetail = {
  slug: "cocina",
  title: "Cocina",
  discipline: "cooking",
  description: null,
  stage_count: 2,
  dish_count: 3,
  skill_count: 2,
  stages: [
    {
      position: 1,
      title: "Sin miedo a la estufa",
      description: null,
      dishes_to_unlock: 1,
      dishes: [
        {
          recipe: recipe("huevos", "Huevos a la mexicana"),
          skills: [{ slug: "picar", name: "Picar", tip: "", is_new: true }],
        },
        { recipe: recipe("sopa", "Sopa de fideo"), skills: [] },
      ],
    },
    {
      position: 2,
      title: "Comida de casa",
      description: null,
      dishes_to_unlock: 1,
      dishes: [
        {
          recipe: recipe("bistec", "Bistec con nopales"),
          skills: [
            { slug: "picar", name: "Picar", tip: "", is_new: false },
            { slug: "sellar", name: "Sellar carne", tip: "", is_new: true },
          ],
        },
      ],
    },
  ],
};

beforeEach(() => {
  window.localStorage.clear();
  resetProgressCache();
});

afterEach(() => vi.restoreAllMocks());

describe("PathLadder", () => {
  it("marks dishes as cooked, unlocks the next stage and lists learned skills", async () => {
    const user = userEvent.setup();
    render(<PathLadder path={path} />);
    const [first, second] = screen
      .getAllByRole("listitem")
      .filter((li) => li.tagName === "LI" && li.querySelector("h2"));

    expect(within(second).getByLabelText("Bloqueada")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");

    const toggle = within(first).getAllByRole("button", { name: "Ya lo cociné" })[0];
    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-pressed", "true");
    expect(within(second).queryByLabelText("Bloqueada")).not.toBeInTheDocument();
    expect(second).toHaveAttribute("aria-current", "step");
    expect(screen.getByText("Habilidades que ya tienes").parentElement).toHaveTextContent("Picar");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "33");
    expect(JSON.parse(window.localStorage.getItem("miseo:cooked:v1") ?? "{}")).toHaveProperty(
      "huevos",
    );
  });

  it("highlights skills that are new in a dish", () => {
    render(<PathLadder path={path} />);
    const fresh = screen
      .getAllByTitle("Habilidad nueva en este platillo")
      .map((el) => el.textContent);
    expect(fresh).toEqual(["Picar", "Sellar carne"]);
    expect(screen.getAllByTitle("Repasas esta habilidad")[0]).toHaveTextContent("Picar");
  });

  it("keeps working when storage is unavailable", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });
    const user = userEvent.setup();
    render(<PathLadder path={path} />);

    const toggle = screen.getAllByRole("button", { name: "Ya lo cociné" })[0];
    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });
});
