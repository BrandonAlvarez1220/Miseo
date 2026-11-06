import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Ingredient, IngredientRef } from "@/types/api";

import { IngredientPicker } from "./ingredient-picker";
import type { PantryParams } from "./search-params";

const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

const ingredient = (slug: string, name: string): Ingredient => ({
  id: slug,
  slug,
  name,
  category: null,
  is_staple: false,
  is_alcoholic: false,
  recipe_count: 1,
});

const params: PantryParams = {
  ingredients: ["pollo"],
  mode: "flexible",
  recipeType: null,
  assumeStaples: true,
};
const selected: IngredientRef[] = [{ id: "pollo", slug: "pollo", name: "Pollo" }];

beforeEach(() => {
  replace.mockReset();
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        Response.json([
          ingredient("arroz", "Arroz"),
          ingredient("arroz-integral", "Arroz integral"),
        ]),
      ),
    ),
  );
});

afterEach(() => vi.unstubAllGlobals());

describe("IngredientPicker", () => {
  it("adds an ingredient from the autocomplete with the keyboard", async () => {
    const user = userEvent.setup();
    render(<IngredientPicker params={params} selected={selected} suggestions={[]} />);

    await user.type(screen.getByRole("combobox"), "arr");
    await screen.findByRole("option", { name: /Arroz integral/ });
    await user.keyboard("{ArrowDown}{Enter}");

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/que-puedo-preparar?i=pollo,arroz-integral", {
        scroll: false,
      }),
    );
    expect(fetch).toHaveBeenCalledWith("/api/ingredients?q=arr", expect.anything());
  });

  it("does not offer ingredients that are already selected", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(Response.json([ingredient("pollo", "Pollo")]))),
    );
    const user = userEvent.setup();
    render(<IngredientPicker params={params} selected={selected} suggestions={[]} />);

    await user.type(screen.getByRole("combobox"), "pol");

    expect(await screen.findByText("Sin resultados para “pol”")).toBeInTheDocument();
  });

  it("shows an error when the search fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(null, { status: 502 }))),
    );
    vi.spyOn(console, "error").mockImplementation(() => {});
    const user = userEvent.setup();
    render(<IngredientPicker params={params} selected={selected} suggestions={[]} />);

    await user.type(screen.getByRole("combobox"), "arr");

    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos buscar ingredientes");
  });

  it("removes a selected ingredient and changes the mode", async () => {
    const user = userEvent.setup();
    render(<IngredientPicker params={params} selected={selected} suggestions={[]} />);

    await user.click(screen.getByRole("button", { name: /Descubrir/ }));
    expect(replace).toHaveBeenLastCalledWith("/que-puedo-preparar?i=pollo&modo=discover", {
      scroll: false,
    });

    await user.click(screen.getByRole("button", { name: "Quitar Pollo" }));
    expect(replace).toHaveBeenLastCalledWith("/que-puedo-preparar", { scroll: false });
  });

  it("adds a suggested ingredient with one tap", async () => {
    const user = userEvent.setup();
    render(
      <IngredientPicker
        params={params}
        selected={selected}
        suggestions={[ingredient("pollo", "Pollo"), ingredient("tomate", "Tomate")]}
      />,
    );

    const suggestions = screen.getByRole("list", { name: "Ingredientes sugeridos" });
    // Already-selected ingredients are not suggested again.
    expect(suggestions).not.toHaveTextContent("Pollo");
    await user.click(screen.getByRole("button", { name: "Tomate" }));

    expect(replace).toHaveBeenCalledWith("/que-puedo-preparar?i=pollo,tomate", { scroll: false });
  });
});
