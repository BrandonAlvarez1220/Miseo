import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Recommendation } from "@/types/api";

import { RecommendationCard } from "./recommendation-card";

const ref = (slug: string, name: string) => ({ id: slug, slug, name });

const item: Recommendation = {
  recipe: {
    id: "r1",
    slug: "pollo-a-la-lima",
    title: "Pollo a la lima",
    description: null,
    image_url: null,
    recipe_type: "cooking",
    difficulty: "easy",
    servings: 2,
    preparation_time_minutes: 10,
    cooking_time_minutes: 20,
    total_time_minutes: 30,
    categories: [{ slug: "carnes-y-aves", name: "Carnes y aves" }],
    ingredient_count: 4,
    is_alcoholic: null,
    published_at: null,
  },
  match_percentage: 63,
  available_ingredients: [ref("pollo", "Pollo")],
  missing_ingredients: [ref("ajo", "Ajo")],
  substitutions: [
    {
      missing: ref("lima", "Lima"),
      substitute: ref("limon", "Limón"),
      substitution_type: "similar",
      ratio: "1.000",
      notes: null,
    },
  ],
  assumed_staples: [ref("sal", "Sal")],
  optional_available: [],
  optional_missing: [],
};

describe("RecommendationCard", () => {
  it("shows match, available, missing ingredients and substitutions", () => {
    render(<RecommendationCard item={item} />);

    expect(screen.getByRole("img", { name: "63% de coincidencia" })).toBeInTheDocument();
    expect(screen.getByText(/Tienes:/).parentElement).toHaveTextContent("Pollo");
    expect(screen.getByText(/Te falta:/).parentElement).toHaveTextContent("Ajo");
    expect(screen.getByText(/usa/).parentElement).toHaveTextContent(
      "Sin Lima: usa Limón (similar)",
    );
    expect(screen.getByText(/Damos por hecho/)).toHaveTextContent("Sal");
    expect(screen.getByText("30 min")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Pollo a la lima" })).toHaveAttribute(
      "href",
      "/recetas/pollo-a-la-lima",
    );
  });
});
