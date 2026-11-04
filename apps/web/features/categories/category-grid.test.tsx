import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Category } from "@/types/api";

import { CategoryGrid } from "./category-grid";

const categories: Category[] = [
  { id: "1", name: "Sours", slug: "sours", description: "Cítrico y dulzor.", recipe_type: "drink" },
  { id: "2", name: "Highballs", slug: "highballs", description: null, recipe_type: "drink" },
];

describe("CategoryGrid", () => {
  it("renders one item per category with its description", () => {
    render(<CategoryGrid categories={categories} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("Sours")).toBeInTheDocument();
    expect(screen.getByText("Cítrico y dulzor.")).toBeInTheDocument();
  });

  it("shows an empty state when there are no categories", () => {
    render(<CategoryGrid categories={[]} />);

    expect(screen.getByRole("status")).toHaveTextContent("Todavía no hay categorías");
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });
});
