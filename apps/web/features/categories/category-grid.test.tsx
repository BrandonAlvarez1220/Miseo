import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Category } from "@/types/api";

import { CategoryGrid } from "./category-grid";

const categories: Category[] = [
  {
    id: "1",
    name: "Sours",
    slug: "sours",
    description: "Cítrico y dulzor.",
    recipe_type: "drink",
    recipe_count: 4,
  },
  {
    id: "2",
    name: "Highballs",
    slug: "highballs",
    description: null,
    recipe_type: "drink",
    recipe_count: 1,
  },
];

describe("CategoryGrid", () => {
  it("links each category to the filtered recipe search with its count", () => {
    render(<CategoryGrid categories={categories} />);

    const sours = screen.getByRole("link", { name: /Sours/ });
    expect(sours).toHaveAttribute("href", "/recetas?tipo=drink&categoria=sours");
    expect(sours).toHaveTextContent("4 recetas");
    expect(screen.getByRole("link", { name: /Highballs/ })).toHaveTextContent("1 receta");
  });

  it("shows an empty state when there are no categories", () => {
    render(<CategoryGrid categories={[]} />);

    expect(screen.getByRole("status")).toHaveTextContent("Todavía no hay categorías");
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
