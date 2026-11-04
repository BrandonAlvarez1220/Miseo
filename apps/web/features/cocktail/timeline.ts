import { TECHNIQUE_CAPTIONS, type LiquidPour, type PourPlan, type SolidAdd } from "./pour-plan";

/**
 * The animation is a list of "beats". Each beat is a full snapshot of the scene;
 * the renderer only interpolates between consecutive snapshots. Keeping the
 * script declarative makes it testable and lets users step through it manually.
 */

export type Vessel = "shaker" | "mixing-glass";
export type Action = "pour" | "shake" | "stir" | "muddle" | "strain" | "stir-glass" | null;

export interface Layer {
  color: string;
  ml: number;
}

export interface Scene {
  vessel: Vessel | null;
  vesselLayers: Layer[];
  vesselMixed: boolean;
  vesselIce: boolean;
  glassLayers: Layer[];
  glassMixed: boolean;
  glassIce: boolean;
  solids: SolidAdd[];
  action: Action;
  pour: { color: string; target: "vessel" | "glass" } | null;
  garnish: boolean;
  bubbles: boolean;
}

export interface Beat {
  caption: string;
  durationMs: number;
  scene: Scene;
}

const DURATIONS = {
  intro: 700,
  solid: 900,
  pour: 1100,
  ice: 800,
  shake: 1900,
  stir: 1700,
  muddle: 1500,
  strain: 1500,
  stirGlass: 1100,
  garnish: 1000,
};

function vesselFor(plan: PourPlan): Vessel | null {
  if (plan.technique === "shake" || plan.technique === "blend") return "shaker";
  if (plan.technique === "stir") return "mixing-glass";
  return null;
}

export function buildTimeline(plan: PourPlan): Beat[] {
  const vessel = vesselFor(plan);
  const beats: Beat[] = [];
  let scene: Scene = {
    vessel,
    vesselLayers: [],
    vesselMixed: false,
    vesselIce: false,
    glassLayers: [],
    glassMixed: false,
    glassIce: false,
    solids: [],
    action: null,
    pour: null,
    garnish: false,
    bubbles: false,
  };
  const push = (caption: string, durationMs: number, changes: Partial<Scene>) => {
    scene = { ...scene, action: null, pour: null, ...changes };
    beats.push({ caption, durationMs, scene });
  };

  push(
    vessel === "shaker"
      ? "Prepara la coctelera"
      : vessel
        ? "Prepara el vaso mezclador"
        : "Prepara el vaso",
    DURATIONS.intro,
    {},
  );

  const solids = plan.steps.filter((s): s is SolidAdd => s.kind === "solid");
  const liquids = plan.steps.filter((s): s is LiquidPour => s.kind === "liquid");
  const mainLiquids = liquids.filter((l) => !l.topUp);
  const topUps = liquids.filter((l) => l.topUp);

  // Solids (mint, sugar cube...) always go into the serving glass first.
  for (const solid of solids) {
    push(solid.label, DURATIONS.solid, { solids: [...scene.solids, solid] });
  }
  if (plan.technique === "muddle" && solids.length) {
    push(TECHNIQUE_CAPTIONS.muddle, DURATIONS.muddle, { action: "muddle" });
  }

  // Built and muddled drinks: fill the glass with ice before pouring (bar practice).
  if (!vessel && plan.ice) push("Llena el vaso de hielo", DURATIONS.ice, { glassIce: true });

  const target = vessel ? "vessel" : "glass";
  for (const liquid of mainLiquids) {
    const layer = { color: liquid.color, ml: liquid.ml };
    push(liquid.label, DURATIONS.pour, {
      action: "pour",
      pour: { color: liquid.color, target },
      ...(vessel
        ? { vesselLayers: [...scene.vesselLayers, layer] }
        : { glassLayers: [...scene.glassLayers, layer] }),
    });
  }

  if (vessel) {
    push("Añade hielo", DURATIONS.ice, { vesselIce: true });
    push(
      TECHNIQUE_CAPTIONS[plan.technique],
      vessel === "shaker" ? DURATIONS.shake : DURATIONS.stir,
      {
        action: vessel === "shaker" ? "shake" : "stir",
        vesselMixed: true,
      },
    );
    if (plan.ice) push("Llena el vaso de hielo", DURATIONS.ice, { glassIce: true });
    push(plan.ice ? "Cuela sobre el hielo" : "Cuela en la copa fría", DURATIONS.strain, {
      action: "strain",
      pour: { color: plan.mixedColor, target: "glass" },
      vesselLayers: [],
      glassLayers: scene.vesselLayers,
      glassMixed: true,
    });
  }

  for (const liquid of topUps) {
    push(liquid.label, DURATIONS.pour, {
      action: "pour",
      pour: { color: liquid.color, target: "glass" },
      glassLayers: [...scene.glassLayers, { color: liquid.color, ml: liquid.ml }],
    });
  }

  if (!vessel && plan.technique !== "float" && scene.glassLayers.length > 1) {
    push(TECHNIQUE_CAPTIONS.build, DURATIONS.stirGlass, { action: "stir-glass", glassMixed: true });
  }

  push(plan.garnishes.length ? "Decora y sirve" : "¡Listo para servir!", DURATIONS.garnish, {
    garnish: true,
    bubbles: plan.carbonated,
  });
  return beats;
}

/** Total liquid in a list of layers. */
export function totalMl(layers: Layer[]): number {
  return layers.reduce((sum, layer) => sum + layer.ml, 0);
}
