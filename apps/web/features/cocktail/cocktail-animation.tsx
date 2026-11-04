"use client";

import { ChevronLeft, ChevronRight, Pause, Play, RotateCcw } from "lucide-react";
import { inView } from "motion";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";
import type { DrinkDetails, RecipeIngredient } from "@/types/api";

import { glassShape, VESSELS, type GlassShape } from "./glasses";
import { buildPourPlan, type GarnishKind, type PourPlan, type SolidAdd } from "./pour-plan";
import { buildTimeline, totalMl, type Layer, type Scene } from "./timeline";

interface CocktailAnimationProps {
  title: string;
  drink: Pick<DrinkDetails, "glass" | "technique" | "garnish">;
  ingredients: RecipeIngredient[];
}

const VESSEL_X = 10;
const GLASS_X_WITH_VESSEL = 230;

/**
 * Data-driven pour animation: glass, technique, volumes and colors all come from
 * the recipe, so every cocktail animates without hand-made assets.
 */
export function CocktailAnimation({ title, drink, ingredients }: CocktailAnimationProps) {
  const plan = useMemo(() => buildPourPlan(drink, ingredients), [drink, ingredients]);
  const beats = useMemo(() => buildTimeline(plan), [plan]);
  const reduceMotion = useReducedMotion();
  const container = useRef<HTMLDivElement>(null);
  const captionId = useId();

  const last = beats.length - 1;
  const [index, setIndex] = useState(0);
  const [playRequested, setPlayRequested] = useState(false);
  // Derived: playback stops by itself on the last beat.
  const playing = playRequested && index < last;

  // Autoplay once when the animation scrolls into view; with reduced motion,
  // show the finished drink instead (the user can still press play).
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    return inView(
      element,
      () => {
        if (reduceMotion) setIndex(last);
        else setPlayRequested(true);
      },
      { amount: 0.4 },
    );
  }, [reduceMotion, last]);

  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => setIndex((i) => Math.min(i + 1, last)), beats[index].durationMs);
    return () => clearTimeout(timer);
  }, [playing, index, last, beats]);

  const setPlaying = setPlayRequested;

  const beat = beats[index];
  const scene = beat.scene;
  const glass = glassShape(plan.glass);
  const width = scene.vessel ? 480 : 240;
  const glassX = scene.vessel ? GLASS_X_WITH_VESSEL : 0;
  const instant = reduceMotion ? { duration: 0 } : undefined;

  function restart() {
    setIndex(0);
    setPlaying(true);
  }

  return (
    <div ref={container} className="rounded-xl border border-line bg-surface p-4 sm:p-6">
      <svg
        viewBox={`0 0 ${width} 300`}
        className="mx-auto block h-72 w-full max-w-xl sm:h-80"
        role="img"
        aria-labelledby={captionId}
      >
        <title>{`Animación de preparación: ${title}`}</title>
        {scene.vessel ? (
          <VesselView x={VESSEL_X} scene={scene} plan={plan} transition={instant} beatKey={index} />
        ) : null}
        <GlassView
          x={glassX}
          glass={glass}
          scene={scene}
          plan={plan}
          transition={instant}
          beatKey={index}
        />
      </svg>

      <p
        id={captionId}
        aria-live="polite"
        className="mt-3 min-h-7 text-center text-lg font-semibold text-pretty"
      >
        {beat.caption}
      </p>

      <div className="mt-4 flex items-center justify-center gap-2">
        <ControlButton
          label="Paso anterior"
          onClick={() => {
            setPlaying(false);
            setIndex((i) => Math.max(0, i - 1));
          }}
          disabled={index === 0}
        >
          <ChevronLeft />
        </ControlButton>
        {playing ? (
          <ControlButton label="Pausar" onClick={() => setPlaying(false)} primary>
            <Pause />
          </ControlButton>
        ) : index >= last ? (
          <ControlButton label="Repetir" onClick={restart} primary>
            <RotateCcw />
          </ControlButton>
        ) : (
          <ControlButton label="Reproducir" onClick={() => setPlaying(true)} primary>
            <Play />
          </ControlButton>
        )}
        <ControlButton
          label="Paso siguiente"
          onClick={() => {
            setPlaying(false);
            setIndex((i) => Math.min(last, i + 1));
          }}
          disabled={index >= last}
        >
          <ChevronRight />
        </ControlButton>
      </div>

      <ol className="mt-5 grid gap-1.5 text-sm sm:grid-cols-2" aria-label="Pasos de la animación">
        {beats.map((b, i) => (
          <li key={`${i}-${b.caption}`}>
            <button
              type="button"
              onClick={() => {
                setPlaying(false);
                setIndex(i);
              }}
              aria-current={i === index ? "step" : undefined}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition-colors",
                i === index
                  ? "bg-primary-soft font-semibold text-primary"
                  : "text-ink-muted hover:text-ink",
              )}
            >
              <span
                className={cn(
                  "flex size-5 shrink-0 items-center justify-center rounded-full text-[11px]",
                  i <= index ? "bg-primary text-primary-ink" : "bg-surface-muted",
                )}
              >
                {i + 1}
              </span>
              {b.caption}
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

function ControlButton({
  label,
  onClick,
  disabled,
  primary,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  primary?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-full transition-colors disabled:opacity-40 [&_svg]:size-5",
        primary
          ? "size-12 bg-primary text-primary-ink hover:bg-primary-hover"
          : "size-10 border border-line hover:bg-surface-muted",
      )}
    >
      {children}
    </button>
  );
}

type Transition = { duration: number } | undefined;

interface LiquidProps {
  clipId: string;
  layers: Layer[];
  mixed: boolean;
  plan: PourPlan;
  bottom: number;
  pxPerMl: number;
  transition: Transition;
}

/** Stacked layers that cross-fade into one mixed color. */
function Liquid({ clipId, layers, mixed, plan, bottom, pxPerMl, transition }: LiquidProps) {
  const t = transition ?? { duration: 0.9, ease: "easeInOut" as const };
  const total = totalMl(layers) * pxPerMl;
  // Bottom-up offsets of each layer, computed before rendering.
  const offsets = layers.map((_, i) => totalMl(layers.slice(0, i)) * pxPerMl);
  return (
    <g clipPath={`url(#${clipId})`}>
      {layers.map((layer, i) => {
        const height = layer.ml * pxPerMl;
        const y = bottom - offsets[i] - height;
        return (
          <motion.rect
            key={i}
            x={0}
            width={240}
            fill={layer.color}
            initial={{ y: bottom, height: 0, opacity: plan.mixedOpacity }}
            animate={{ y, height, opacity: mixed ? 0 : plan.mixedOpacity }}
            transition={t}
          />
        );
      })}
      <motion.rect
        x={0}
        width={240}
        fill={plan.mixedColor}
        initial={false}
        animate={{ y: bottom - total, height: total, opacity: mixed ? plan.mixedOpacity : 0 }}
        transition={t}
      />
      {/* Surface highlight */}
      <motion.rect
        x={0}
        width={240}
        height={2}
        fill="#ffffff"
        initial={false}
        animate={{ y: bottom - total, opacity: total > 0 ? 0.35 : 0 }}
        transition={t}
      />
    </g>
  );
}

function IceCubes({
  clipId,
  left,
  right,
  bottom,
  show,
  transition,
}: {
  clipId: string;
  left: number;
  right: number;
  bottom: number;
  show: boolean;
  transition: Transition;
}) {
  const size = 24;
  const span = right - left - size;
  const cubes = [
    { x: left + span * 0.1, y: bottom - size - 2, r: -8 },
    { x: left + span * 0.75, y: bottom - size - 4, r: 10 },
    { x: left + span * 0.4, y: bottom - size * 2 + 2, r: 4 },
    { x: left + span * 0.05, y: bottom - size * 2.6, r: 14 },
  ];
  return (
    <g clipPath={`url(#${clipId})`}>
      <AnimatePresence>
        {show
          ? cubes.map((cube, i) => (
              <motion.rect
                key={i}
                width={size}
                height={size}
                rx={6}
                x={cube.x}
                fill="#ffffff"
                fillOpacity={0.35}
                stroke="#ffffff"
                strokeOpacity={0.7}
                initial={{ y: bottom - 260, rotate: 0, opacity: 0 }}
                animate={{ y: cube.y, rotate: cube.r, opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={
                  transition ?? { type: "spring", stiffness: 180, damping: 16, delay: i * 0.12 }
                }
                style={{ transformBox: "fill-box", transformOrigin: "center" }}
              />
            ))
          : null}
      </AnimatePresence>
    </g>
  );
}

function Solids({
  solids,
  glass,
  transition,
}: {
  solids: SolidAdd[];
  glass: GlassShape;
  transition: Transition;
}) {
  const center = (glass.iceLeft + glass.iceRight) / 2;
  return (
    <g>
      {solids.flatMap((solid, s) =>
        Array.from({ length: solid.count }, (_, i) => {
          const x = center - 30 + ((i * 17 + s * 9) % 60);
          const y = glass.bottom - 8 - (i % 2) * 6;
          const common = {
            initial: { y: -200, opacity: 0 },
            animate: { y: 0, opacity: 1 },
            transition: transition ?? {
              type: "spring" as const,
              stiffness: 140,
              damping: 18,
              delay: i * 0.06,
            },
          };
          if (solid.shape === "leaf") {
            return (
              <motion.ellipse
                key={`${s}-${i}`}
                cx={x}
                cy={y}
                rx={9}
                ry={4.5}
                fill={solid.color}
                transform={`rotate(${((i * 37) % 70) - 35} ${x} ${y})`}
                {...common}
              />
            );
          }
          if (solid.shape === "slice") {
            return (
              <motion.circle
                key={`${s}-${i}`}
                cx={x}
                cy={y - 4}
                r={8}
                fill={solid.color}
                {...common}
              />
            );
          }
          return (
            <motion.rect
              key={`${s}-${i}`}
              x={x - 7}
              y={y - 12}
              width={14}
              height={14}
              rx={2}
              fill={solid.color}
              {...common}
            />
          );
        }),
      )}
    </g>
  );
}

function Bubbles({ clipId, glass, show }: { clipId: string; glass: GlassShape; show: boolean }) {
  if (!show) return null;
  const bubbles = Array.from({ length: 10 }, (_, i) => ({
    x: glass.iceLeft + ((i * 23) % (glass.iceRight - glass.iceLeft)),
    r: 1.5 + (i % 3),
    delay: (i * 0.37) % 2.4,
  }));
  return (
    <g clipPath={`url(#${clipId})`}>
      {bubbles.map((b, i) => (
        <motion.circle
          key={i}
          cx={b.x}
          r={b.r}
          fill="#ffffff"
          fillOpacity={0.7}
          initial={{ cy: glass.bottom, opacity: 0 }}
          animate={{ cy: glass.fullTop, opacity: [0, 0.9, 0] }}
          transition={{ duration: 2.4, repeat: Infinity, delay: b.delay, ease: "easeOut" }}
        />
      ))}
    </g>
  );
}

function Garnish({
  kinds,
  glass,
  show,
  transition,
}: {
  kinds: GarnishKind[];
  glass: GlassShape;
  show: boolean;
  transition: Transition;
}) {
  const appear = {
    initial: { scale: 0, opacity: 0 },
    animate: show ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 },
    transition: transition ?? { type: "spring" as const, stiffness: 220, damping: 14 },
    style: { transformBox: "fill-box" as const, transformOrigin: "center" },
  };
  const right = glass.rimRight;
  const y = glass.rimY;
  return (
    <g>
      {kinds.includes("salt-rim") ? (
        <motion.path
          d={`M${glass.rimLeft + 2} ${y} L${(glass.rimLeft + right) / 2} ${y}`}
          stroke="#ffffff"
          strokeWidth={5}
          strokeDasharray="2 3"
          strokeLinecap="round"
          {...appear}
        />
      ) : null}
      {kinds.includes("citrus-wheel") ? (
        <motion.g {...appear}>
          <circle
            cx={right - 4}
            cy={y + 2}
            r={19}
            fill="#c9dd7a"
            stroke="#7fa33a"
            strokeWidth={3}
          />
          <path
            d={`M${right - 4} ${y - 15} V${y + 19} M${right - 21} ${y + 2} H${right + 13} M${right - 16} ${y - 10} L${right + 8} ${y + 14} M${right + 8} ${y - 10} L${right - 16} ${y + 14}`}
            stroke="#eef5cf"
            strokeWidth={1.5}
          />
        </motion.g>
      ) : null}
      {kinds.includes("orange-peel") ? (
        <motion.path
          d={`M${glass.rimLeft + 18} ${y - 2} q12 -20 26 -6 q10 10 22 -6`}
          stroke="#f59e3c"
          strokeWidth={6}
          fill="none"
          strokeLinecap="round"
          {...appear}
        />
      ) : null}
      {kinds.includes("mint") ? (
        <motion.g {...appear}>
          <path d={`M120 ${y + 4} V${y - 26}`} stroke="#2f7a3a" strokeWidth={2} />
          <ellipse
            cx={111}
            cy={y - 18}
            rx={10}
            ry={5}
            fill="#3c9a48"
            transform={`rotate(-30 111 ${y - 18})`}
          />
          <ellipse
            cx={129}
            cy={y - 22}
            rx={10}
            ry={5}
            fill="#46aa52"
            transform={`rotate(25 129 ${y - 22})`}
          />
          <ellipse
            cx={120}
            cy={y - 32}
            rx={9}
            ry={4.5}
            fill="#3c9a48"
            transform={`rotate(-80 120 ${y - 32})`}
          />
        </motion.g>
      ) : null}
      {kinds.includes("cherry") ? (
        <motion.g {...appear}>
          <path
            d={`M${glass.rimLeft + 30} ${y - 4} q6 -18 18 -24`}
            stroke="#5a3a1a"
            strokeWidth={2}
            fill="none"
          />
          <circle cx={glass.rimLeft + 30} cy={y} r={8} fill="#b3122e" />
        </motion.g>
      ) : null}
    </g>
  );
}

function PourStream({
  x,
  surfaceY,
  color,
  show,
  beatKey,
}: {
  x: number;
  surfaceY: number;
  color: string;
  show: boolean;
  beatKey: number;
}) {
  return (
    <AnimatePresence>
      {show ? (
        <motion.rect
          key={beatKey}
          x={x - 3}
          y={0}
          width={6}
          rx={3}
          fill={color}
          fillOpacity={0.85}
          initial={{ height: 0 }}
          animate={{ height: [0, surfaceY, surfaceY, 0], y: [0, 0, 0, surfaceY] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1, times: [0, 0.3, 0.75, 1] }}
        />
      ) : null}
    </AnimatePresence>
  );
}

function BarSpoon({
  x,
  top,
  bottom,
  active,
}: {
  x: number;
  top: number;
  bottom: number;
  active: boolean;
}) {
  return (
    <AnimatePresence>
      {active ? (
        <motion.g
          key="bar-spoon"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, x: [0, -12, 12, -12, 12, 0] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.5 }}
        >
          <path
            d={`M${x} ${top} L${x} ${bottom}`}
            stroke="#c9ccd1"
            strokeWidth={3}
            strokeLinecap="round"
          />
          <ellipse cx={x} cy={bottom} rx={5} ry={3} fill="#c9ccd1" />
        </motion.g>
      ) : null}
    </AnimatePresence>
  );
}

function Muddler({ x, bottom, active }: { x: number; bottom: number; active: boolean }) {
  return (
    <AnimatePresence>
      {active ? (
        <motion.rect
          key="muddler"
          x={x - 7}
          width={14}
          height={120}
          rx={6}
          fill="#a87b4f"
          initial={{ y: bottom - 220, opacity: 0 }}
          animate={{
            y: [
              bottom - 200,
              bottom - 122,
              bottom - 170,
              bottom - 122,
              bottom - 170,
              bottom - 122,
              bottom - 200,
            ],
            opacity: 1,
          }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.4 }}
        />
      ) : null}
    </AnimatePresence>
  );
}

interface ViewProps {
  x: number;
  scene: Scene;
  plan: PourPlan;
  transition: Transition;
  beatKey: number;
}

function GlassView({
  x,
  glass,
  scene,
  plan,
  transition,
  beatKey,
}: ViewProps & { glass: GlassShape }) {
  const clipId = useId();
  const allLiquid = plan.steps.reduce((sum, s) => (s.kind === "liquid" ? sum + s.ml : sum), 0);
  const pxPerMl = allLiquid > 0 ? (glass.bottom - glass.fullTop) / allLiquid : 0;
  const surfaceY = glass.bottom - totalMl(scene.glassLayers) * pxPerMl;
  const center = (glass.rimLeft + glass.rimRight) / 2;
  return (
    <g transform={`translate(${x} 0)`}>
      <defs>
        <clipPath id={clipId}>
          <path d={glass.interior} />
        </clipPath>
      </defs>
      <path d={glass.interior} fill="#ffffff" fillOpacity={0.05} />
      <Solids solids={scene.solids} glass={glass} transition={transition} />
      <Liquid
        clipId={clipId}
        layers={scene.glassLayers}
        mixed={scene.glassMixed}
        plan={plan}
        bottom={glass.bottom}
        pxPerMl={pxPerMl}
        transition={transition}
      />
      <IceCubes
        clipId={clipId}
        left={glass.iceLeft}
        right={glass.iceRight}
        bottom={glass.bottom}
        show={scene.glassIce}
        transition={transition}
      />
      <Bubbles clipId={clipId} glass={glass} show={scene.bubbles} />
      {glass.bodyFill ? <path d={glass.outline} fill={glass.bodyFill} fillOpacity={0.55} /> : null}
      <path
        d={glass.outline}
        fill="none"
        stroke="currentColor"
        strokeOpacity={0.55}
        strokeWidth={3}
        strokeLinejoin="round"
        className="text-ink"
      />
      {glass.details.map((d) => (
        <path
          key={d}
          d={d}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.55}
          strokeWidth={3}
          strokeLinecap="round"
          className="text-ink"
        />
      ))}
      {/* Glass reflection */}
      <path
        d={`M${glass.rimLeft + 12} ${glass.rimY + 14} l-2 ${Math.min(70, glass.bottom - glass.rimY - 30)}`}
        stroke="#ffffff"
        strokeOpacity={0.25}
        strokeWidth={4}
        strokeLinecap="round"
      />
      <Muddler x={center} bottom={glass.bottom} active={scene.action === "muddle"} />
      <BarSpoon
        x={center + 14}
        top={glass.rimY - 30}
        bottom={glass.bottom - 12}
        active={scene.action === "stir-glass"}
      />
      <PourStream
        x={center}
        surfaceY={surfaceY}
        color={scene.pour?.color ?? "#ffffff"}
        show={scene.pour?.target === "glass"}
        beatKey={beatKey}
      />
      <Garnish kinds={plan.garnishes} glass={glass} show={scene.garnish} transition={transition} />
    </g>
  );
}

function VesselView({ x, scene, plan, transition, beatKey }: ViewProps) {
  const clipId = useId();
  const vessel = VESSELS[scene.vessel ?? "shaker"];
  const mainLiquid = plan.steps.reduce(
    (sum, s) => (s.kind === "liquid" && !s.topUp ? sum + s.ml : sum),
    0,
  );
  const pxPerMl = mainLiquid > 0 ? (vessel.bottom - vessel.fullTop) / mainLiquid : 0;
  const shaking = scene.action === "shake";
  const straining = scene.action === "strain";
  // Keep the mixed color visible while straining so the vessel visibly empties.
  const layers = straining ? [] : scene.vesselLayers;
  const surfaceY = vessel.bottom - totalMl(layers) * pxPerMl;
  return (
    <g transform={`translate(${x} 0)`}>
      <motion.g
        animate={
          shaking
            ? { rotate: [0, -14, 12, -14, 12, -10, 8, 0], y: [0, -16, 0, -16, 0, -12, 0, 0] }
            : straining
              ? { rotate: 58, x: 70, y: -40 }
              : { rotate: 0, x: 0, y: 0 }
        }
        transition={transition ?? { duration: shaking ? 1.7 : 0.6 }}
        style={{ transformBox: "fill-box", transformOrigin: "center" }}
      >
        <defs>
          <clipPath id={clipId}>
            <path d={vessel.interior} />
          </clipPath>
        </defs>
        <Liquid
          clipId={clipId}
          layers={layers}
          mixed={scene.vesselMixed}
          plan={plan}
          bottom={vessel.bottom}
          pxPerMl={pxPerMl}
          transition={transition}
        />
        <IceCubes
          clipId={clipId}
          left={76}
          right={144}
          bottom={vessel.bottom}
          show={scene.vesselIce}
          transition={transition}
        />
        <path
          d={vessel.outline}
          fill="#c9ccd1"
          fillOpacity={scene.vessel === "shaker" ? 0.25 : 0.06}
          stroke="currentColor"
          strokeOpacity={0.55}
          strokeWidth={3}
          strokeLinejoin="round"
          className="text-ink"
        />
        {vessel.cap ? (
          <AnimatePresence>
            {shaking ? (
              <motion.path
                key="shaker-cap"
                d={vessel.cap}
                fill="#c9ccd1"
                fillOpacity={0.5}
                stroke="currentColor"
                strokeOpacity={0.55}
                strokeWidth={3}
                className="text-ink"
                initial={{ y: -40, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -40, opacity: 0 }}
              />
            ) : null}
          </AnimatePresence>
        ) : null}
        <BarSpoon x={118} top={60} bottom={vessel.bottom - 14} active={scene.action === "stir"} />
      </motion.g>
      <PourStream
        x={110}
        surfaceY={surfaceY}
        color={scene.pour?.color ?? "#ffffff"}
        show={scene.pour?.target === "vessel"}
        beatKey={beatKey}
      />
    </g>
  );
}
