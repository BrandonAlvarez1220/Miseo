import { describe, expect, it } from "vitest";

import type { PourPlan } from "./pour-plan";
import { buildTimeline } from "./timeline";

const plan = (overrides: Partial<PourPlan>): PourPlan => ({
  glass: "coupe",
  technique: "shake",
  steps: [],
  mixedColor: "#eeeeee",
  mixedOpacity: 0.5,
  carbonated: false,
  ice: false,
  garnishes: [],
  ...overrides,
});

const pour = (name: string, ml: number, topUp = false) => ({
  kind: "liquid" as const,
  name,
  ml,
  topUp,
  color: "#ffffff",
  label: topUp ? `Completa con ${name}` : `Vierte ${ml} ml de ${name}`,
});

describe("buildTimeline", () => {
  it("shaken drinks: pour into shaker, ice, shake, strain into the glass", () => {
    const beats = buildTimeline(plan({ steps: [pour("ron", 60), pour("lima", 20)] }));

    expect(beats.map((b) => b.caption)).toEqual([
      "Prepara la coctelera",
      "Vierte 60 ml de ron",
      "Vierte 20 ml de lima",
      "Añade hielo",
      "Bate con energía con hielo",
      "Cuela en la copa fría",
      "¡Listo para servir!",
    ]);
    const strain = beats[5].scene;
    expect(strain.vesselLayers).toEqual([]);
    expect(strain.glassMixed).toBe(true);
    expect(strain.glassLayers.map((l) => l.ml)).toEqual([60, 20]);
  });

  it("built highballs: ice first, top up last, then a gentle stir", () => {
    const beats = buildTimeline(
      plan({
        glass: "highball",
        technique: "build",
        ice: true,
        carbonated: true,
        garnishes: ["citrus-wheel"],
        steps: [pour("ron", 50), pour("cola", 100, true)],
      }),
    );

    expect(beats.map((b) => b.caption)).toEqual([
      "Prepara el vaso",
      "Llena el vaso de hielo",
      "Vierte 50 ml de ron",
      "Completa con cola",
      "Remueve suavemente",
      "Decora y sirve",
    ]);
    expect(beats.at(-1)?.scene).toMatchObject({ bubbles: true, garnish: true, glassMixed: true });
    expect(beats.every((b) => b.scene.vessel === null)).toBe(true);
  });

  it("muddled drinks add solids and muddle before pouring", () => {
    const beats = buildTimeline(
      plan({
        glass: "highball",
        technique: "muddle",
        ice: true,
        steps: [
          {
            kind: "solid",
            name: "menta",
            shape: "leaf",
            count: 6,
            color: "#3c9a48",
            label: "Añade menta",
          },
          pour("ron", 45),
        ],
      }),
    );

    expect(beats.slice(1, 5).map((b) => b.caption)).toEqual([
      "Añade menta",
      "Machaca con suavidad",
      "Llena el vaso de hielo",
      "Vierte 45 ml de ron",
    ]);
    expect(beats[2].scene.action).toBe("muddle");
  });

  it("each beat only animates its own action", () => {
    const beats = buildTimeline(plan({ steps: [pour("ron", 60)] }));
    expect(beats[1].scene.action).toBe("pour");
    expect(beats[2].scene.action).toBeNull();
  });
});
