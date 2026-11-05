import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SubmissionDetail } from "@/types/api";

import { ReviewPanel } from "./review-panel";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const approveAction = vi.fn();
const rejectAction = vi.fn();
vi.mock("./actions", () => ({
  approveAction: (...args: unknown[]) => approveAction(...args),
  rejectAction: (...args: unknown[]) => rejectAction(...args),
}));

const detail: SubmissionDetail = {
  id: "11111111-1111-4111-8111-111111111111",
  status: "needs_review",
  outcome: "created",
  issues: [],
  blocking_issues: 1,
  analysis: {
    difficulty: { score: 1, label: "easy", reasons: [] },
    skills: [{ slug: "sofreir", name: "Sofreír" }],
    placements: [
      {
        path_slug: "cocina",
        path_title: "Ruta de cocina",
        stage_position: 2,
        stage_title: "Comida de casa",
        new_stage: false,
        unknown_skills: [],
        introduces: [],
        reason: "necesita habilidades de la etapa 2",
      },
      {
        path_slug: "otra",
        path_title: "Otra ruta",
        stage_position: 4,
        stage_title: "Nueva etapa",
        new_stage: true,
        unknown_skills: [],
        introduces: [],
        reason: "más difícil que cualquier etapa",
      },
    ],
    duplicates: [],
    classification: null,
  },
  review_notes: null,
  recipe_slug: null,
  title: "Chilaquiles rojos",
  recipe_type: "cooking",
  source: {
    name: "Cocina de ejemplo",
    url: null,
    source_type: "original",
    license: null,
    attribution: null,
  },
  description: null,
  tips: null,
  servings: 2,
  preparation_time_minutes: 10,
  cooking_time_minutes: 20,
  categories: ["desayunos"],
  lines: [
    {
      index: 0,
      name: "tomate",
      ingredient_slug: "tomate",
      ingredient_name: "Tomate",
      candidates: [],
      quantity: "4",
      quantity_max: null,
      unit_code: "piece",
      unit_text: "piece",
      optional: false,
      notes: null,
      group: null,
    },
    {
      index: 1,
      name: "chile guajillo",
      ingredient_slug: null,
      ingredient_name: null,
      candidates: [{ slug: "chile-jalapeno", name: "Chile jalapeño", similarity: 0.5 }],
      quantity: "3",
      quantity_max: null,
      unit_code: "piece",
      unit_text: "piece",
      optional: false,
      notes: null,
      group: null,
    },
  ],
  steps: ["Licúa y fríe."],
  drink: null,
  agent_notes: null,
  agent: null,
  created_at: "2026-11-05T10:00:00Z",
  reviewed_at: null,
};

const catalogs = {
  units: [
    {
      code: "piece",
      name: "pieza",
      plural_name: "piezas",
      unit_type: "count" as const,
      to_base_factor: null,
    },
  ],
  ingredientCategories: [{ slug: "especias", name: "Especias" }],
  categories: [
    {
      id: "1",
      name: "Desayunos",
      slug: "desayunos",
      description: null,
      recipe_type: "cooking" as const,
      recipe_count: 1,
    },
    {
      id: "2",
      name: "Entradas",
      slug: "entradas",
      description: null,
      recipe_type: "cooking" as const,
      recipe_count: 1,
    },
  ],
};

function renderPanel(overrides: Partial<SubmissionDetail> = {}) {
  render(<ReviewPanel detail={{ ...detail, ...overrides }} {...catalogs} />);
}

beforeEach(() => {
  refresh.mockReset();
  approveAction.mockReset().mockResolvedValue({ ok: true });
  rejectAction.mockReset().mockResolvedValue({ ok: true });
});

describe("ReviewPanel", () => {
  it("keeps Approve disabled until every unmatched ingredient has a decision", async () => {
    const user = userEvent.setup();
    renderPanel();
    const approve = screen.getByRole("button", { name: /Aprobar y publicar/ });

    expect(approve).toBeDisabled();
    expect(screen.getByText(/1 ingrediente\(s\) por resolver/)).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: /chile guajillo/ }), "create");
    expect(approve).toBeEnabled();
  });

  it("sends a created ingredient (with its family) and the default placement", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.selectOptions(screen.getByRole("combobox", { name: /chile guajillo/ }), "create");
    await user.selectOptions(screen.getByLabelText("Familia"), "especias");
    await user.click(screen.getByRole("button", { name: /Aprobar y publicar/ }));

    expect(approveAction).toHaveBeenCalledWith(detail.id, {
      ingredient_mappings: {},
      new_ingredients: { "1": { name: "Chile guajillo", category: "especias" } },
      unit_mappings: {},
      categories: ["desayunos"],
      skills: ["sofreir"],
      placement: { path_slug: "cocina", stage_position: 2 },
      review_notes: null,
    });
    expect(refresh).toHaveBeenCalled();
  });

  it("can map to a suggested candidate instead of creating", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.selectOptions(
      screen.getByRole("combobox", { name: /chile guajillo/ }),
      "c:chile-jalapeno",
    );
    await user.click(screen.getByRole("button", { name: /Aprobar y publicar/ }));

    expect(approveAction.mock.calls[0][1]).toMatchObject({
      ingredient_mappings: { "1": "chile-jalapeno" },
      new_ingredients: {},
    });
  });

  it("does not offer a placement on a stage that does not exist yet", () => {
    renderPanel();
    expect(screen.getByRole("radio", { name: /Otra ruta/ })).toBeDisabled();
    expect(screen.getByRole("radio", { name: /Ruta de cocina/ })).toBeChecked();
  });

  it("requires at least one category", async () => {
    const user = userEvent.setup();
    renderPanel({ lines: [detail.lines[0]] });
    expect(screen.getByRole("button", { name: /Aprobar y publicar/ })).toBeEnabled();

    await user.click(screen.getByRole("checkbox", { name: "Desayunos" }));

    expect(screen.getByRole("button", { name: /Aprobar y publicar/ })).toBeDisabled();
    expect(screen.getByText(/elige al menos una categoría/)).toBeInTheDocument();
  });

  it("shows the API's reasons when approval is refused and does not refresh", async () => {
    approveAction.mockResolvedValue({
      ok: false,
      error: "Map every unmatched ingredient",
      details: ["Línea 2: falta resolver el ingrediente «chile guajillo»."],
    });
    const user = userEvent.setup();
    renderPanel({ lines: [detail.lines[0]] });

    await user.click(screen.getByRole("button", { name: /Aprobar y publicar/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Línea 2");
    expect(refresh).not.toHaveBeenCalled();
  });

  it("asks for a reason before rejecting and sends it", async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole("button", { name: /Rechazar/ }));
    const confirm = screen.getByRole("button", { name: "Confirmar rechazo" });
    expect(confirm).toBeDisabled();

    await user.type(screen.getByLabelText(/Motivo del rechazo/), "Duplicada.");
    await user.click(confirm);

    expect(rejectAction).toHaveBeenCalledWith(detail.id, "Duplicada.");
    expect(refresh).toHaveBeenCalled();
  });

  it("only offers 'classic' for drinks that are not AI-generated", () => {
    const drink = {
      is_alcoholic: true,
      base_spirit: null,
      glass: null,
      technique: null,
      garnish: null,
    };
    const analysis = {
      ...detail.analysis!,
      classification: { claimed: "classic" as const, suggested: "experimental" as const },
    };
    const { unmount } = render(
      <ReviewPanel
        detail={{ ...detail, recipe_type: "drink", drink, analysis, lines: [detail.lines[0]] }}
        {...catalogs}
      />,
    );
    expect(screen.getByRole("option", { name: /Clásico/ })).toBeInTheDocument();
    unmount();

    render(
      <ReviewPanel
        detail={{
          ...detail,
          recipe_type: "drink",
          drink,
          analysis,
          lines: [detail.lines[0]],
          source: { ...detail.source, source_type: "ai_generated" },
        }}
        {...catalogs}
      />,
    );
    expect(screen.queryByRole("option", { name: /Clásico/ })).not.toBeInTheDocument();
  });
});
