"use client";

import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useId, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { capitalizeFirst } from "@/lib/format";
import type { Category, SubmissionDetail, SubmissionLine, Unit } from "@/types/api";

import { approveAction, rejectAction, type ActionResult } from "./actions";
import {
  buildApprovePayload,
  unresolvedLines,
  unresolvedUnits,
  type LineChoice,
  type ReviewDecisions,
} from "./approve-payload";

const field =
  "h-10 w-full rounded-md border border-line bg-surface px-3 text-sm focus:border-primary focus:outline-none";

interface ReviewPanelProps {
  detail: SubmissionDetail;
  units: Unit[];
  ingredientCategories: { slug: string; name: string }[];
  categories: Category[];
}

/** Decisions for one submission: resolve unmatched lines, then approve or reject. */
export function ReviewPanel({ detail, units, ingredientCategories, categories }: ReviewPanelProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const firstPlacement = detail.analysis?.placements.find((p) => !p.new_stage);
  const isAiGenerated = detail.source.source_type === "ai_generated";

  const [decisions, setDecisions] = useState<ReviewDecisions>({
    lineChoices: {},
    unitChoices: {},
    categories: detail.categories,
    skills: detail.analysis?.skills.map((skill) => skill.slug) ?? [],
    placement: firstPlacement ? `${firstPlacement.path_slug}:${firstPlacement.stage_position}` : "",
    classification: detail.analysis?.classification?.suggested ?? "",
    notes: "",
  });
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [failure, setFailure] = useState<Extract<ActionResult, { ok: false }> | null>(null);

  const update = (changes: Partial<ReviewDecisions>) => setDecisions((d) => ({ ...d, ...changes }));
  const missingLines = unresolvedLines(detail, decisions.lineChoices);
  const missingUnits = unresolvedUnits(detail, decisions.unitChoices);
  const blockers = [
    ...(missingLines.length ? [`${missingLines.length} ingrediente(s) por resolver`] : []),
    ...(missingUnits.length ? [`${missingUnits.length} unidad(es) por resolver`] : []),
    ...(decisions.categories.length === 0 ? ["elige al menos una categoría"] : []),
  ];

  function run(action: () => Promise<ActionResult>) {
    setFailure(null);
    startTransition(async () => {
      const result = await action();
      if (result.ok) router.refresh();
      else setFailure(result);
    });
  }

  const toggle = (list: string[], value: string) =>
    list.includes(value) ? list.filter((item) => item !== value) : [...list, value];

  return (
    <section
      aria-labelledby="decide"
      className="space-y-5 rounded-lg border-2 border-primary bg-surface p-5"
    >
      <h2 id="decide" className="text-lg font-bold">
        Tu decisión
      </h2>

      {detail.lines.some((line) => !line.ingredient_slug) ? (
        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold">Ingredientes sin coincidencia</legend>
          <p className="text-sm text-ink-muted">
            Mapea cada uno a un ingrediente existente o créalo en el catálogo. Mapear algo distinto
            cambia la receta (por ejemplo, «guajillo» no es «jalapeño»): si no existe, créalo.
          </p>
          {detail.lines
            .filter((line) => !line.ingredient_slug)
            .map((line) => (
              <UnmatchedLine
                key={line.index}
                line={line}
                categories={ingredientCategories}
                onChange={(choice) =>
                  update({ lineChoices: { ...decisions.lineChoices, [line.index]: choice } })
                }
              />
            ))}
        </fieldset>
      ) : null}

      {detail.lines.some((line) => line.unit_text && !line.unit_code) ? (
        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold">Unidades desconocidas</legend>
          {detail.lines
            .filter((line) => line.unit_text && !line.unit_code)
            .map((line) => (
              <label
                key={line.index}
                className="grid gap-1 text-sm sm:grid-cols-[1fr_1fr] sm:items-center"
              >
                <span>
                  Línea {line.index + 1}: «{line.unit_text}» de {line.name}
                </span>
                <select
                  className={field}
                  value={decisions.unitChoices[line.index] ?? ""}
                  onChange={(event) =>
                    update({
                      unitChoices: { ...decisions.unitChoices, [line.index]: event.target.value },
                    })
                  }
                >
                  <option value="">Elige una unidad…</option>
                  {units.map((unit) => (
                    <option key={unit.code} value={unit.code}>
                      {unit.name} ({unit.code})
                    </option>
                  ))}
                </select>
              </label>
            ))}
        </fieldset>
      ) : null}

      <fieldset>
        <legend className="mb-2 text-sm font-semibold">Categorías</legend>
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <label
              key={category.slug}
              className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary-soft"
            >
              <input
                type="checkbox"
                className="accent-[var(--primary)]"
                checked={decisions.categories.includes(category.slug)}
                onChange={() => update({ categories: toggle(decisions.categories, category.slug) })}
              />
              {category.name}
            </label>
          ))}
        </div>
      </fieldset>

      {detail.analysis?.skills.length ? (
        <fieldset>
          <legend className="mb-2 text-sm font-semibold">Habilidades que enseña (sugeridas)</legend>
          <div className="flex flex-wrap gap-2">
            {detail.analysis.skills.map((skill) => (
              <label
                key={skill.slug}
                className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm has-[:checked]:border-primary has-[:checked]:bg-primary-soft"
              >
                <input
                  type="checkbox"
                  className="accent-[var(--primary)]"
                  checked={decisions.skills.includes(skill.slug)}
                  onChange={() => update({ skills: toggle(decisions.skills, skill.slug) })}
                />
                {skill.name}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      {detail.analysis?.placements.length ? (
        <fieldset className="space-y-2">
          <legend className="mb-1 text-sm font-semibold">Colocar en una ruta de aprendizaje</legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="placement"
              className="accent-[var(--primary)]"
              checked={decisions.placement === ""}
              onChange={() => update({ placement: "" })}
            />
            No colocar en ninguna ruta
          </label>
          {detail.analysis.placements.map((placement) => {
            const value = `${placement.path_slug}:${placement.stage_position}`;
            return (
              <label key={value} className="flex items-start gap-2 text-sm">
                <input
                  type="radio"
                  name="placement"
                  className="mt-1 accent-[var(--primary)]"
                  disabled={placement.new_stage}
                  checked={decisions.placement === value}
                  onChange={() => update({ placement: value })}
                />
                <span>
                  {placement.path_title} · etapa {placement.stage_position} «{placement.stage_title}
                  »
                  <span className="block text-xs text-ink-muted">
                    {placement.reason}
                    {placement.new_stage ? " (aún no se pueden crear etapas desde aquí)" : ""}
                    {placement.unknown_skills.length
                      ? ` · habilidades nuevas para la ruta: ${placement.unknown_skills.join(", ")}`
                      : ""}
                  </span>
                </span>
              </label>
            );
          })}
        </fieldset>
      ) : null}

      {detail.recipe_type === "drink" ? (
        <label className="block text-sm font-semibold">
          Clasificación del cóctel
          <select
            className={`${field} mt-1 font-normal`}
            value={decisions.classification}
            onChange={(event) => update({ classification: event.target.value })}
          >
            <option value="experimental">Experimental</option>
            <option value="contemporary">Contemporáneo</option>
            {isAiGenerated ? null : (
              <option value="classic">Clásico (la fuente lo documenta)</option>
            )}
          </select>
          <span className="mt-1 block text-xs font-normal text-ink-muted">
            Un cóctel generado por IA nunca puede publicarse como clásico documentado.
          </span>
        </label>
      ) : null}

      <label className="block text-sm font-semibold">
        Notas de revisión (opcional)
        <textarea
          className="mt-1 min-h-20 w-full rounded-md border border-line bg-surface p-3 text-sm font-normal focus:border-primary focus:outline-none"
          maxLength={2000}
          value={decisions.notes}
          onChange={(event) => update({ notes: event.target.value })}
        />
      </label>

      {failure ? (
        <div role="alert" className="rounded-md bg-danger-soft px-4 py-3 text-sm text-danger">
          <p className="font-semibold">{failure.error}</p>
          {failure.details.length ? (
            <ul className="mt-1 list-inside list-disc">
              {failure.details.map((detailLine) => (
                <li key={detailLine}>{detailLine}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {blockers.length ? (
        <p className="text-sm text-ink-muted">Para aprobar falta: {blockers.join("; ")}.</p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          size="lg"
          disabled={pending || blockers.length > 0}
          onClick={() =>
            run(() => approveAction(detail.id, buildApprovePayload(detail, decisions)))
          }
        >
          {pending && !rejecting ? (
            <Loader2 aria-hidden="true" className="animate-spin" />
          ) : (
            <CheckCircle2 aria-hidden="true" />
          )}
          Aprobar y publicar
        </Button>
        <Button
          variant="outline"
          size="lg"
          disabled={pending}
          onClick={() => setRejecting((v) => !v)}
        >
          <XCircle aria-hidden="true" /> Rechazar
        </Button>
      </div>

      {rejecting ? (
        <div className="space-y-3 rounded-md bg-surface-muted p-4">
          <label className="block text-sm font-semibold">
            Motivo del rechazo (el agente lo leerá)
            <textarea
              className="mt-1 min-h-20 w-full rounded-md border border-line bg-surface p-3 text-sm font-normal focus:border-primary focus:outline-none"
              maxLength={2000}
              value={rejectReason}
              onChange={(event) => setRejectReason(event.target.value)}
            />
          </label>
          <Button
            variant="secondary"
            disabled={pending || rejectReason.trim().length < 3}
            onClick={() => run(() => rejectAction(detail.id, rejectReason))}
          >
            {pending ? <Loader2 aria-hidden="true" className="animate-spin" /> : null}
            Confirmar rechazo
          </Button>
        </div>
      ) : null}
    </section>
  );
}

type Kind = "unset" | "candidate" | "create" | "other";

function UnmatchedLine({
  line,
  categories,
  onChange,
}: {
  line: SubmissionLine;
  categories: { slug: string; name: string }[];
  onChange: (choice: LineChoice) => void;
}) {
  const id = useId();
  const [kind, setKind] = useState<Kind>("unset");
  const [value, setValue] = useState(""); // chosen slug, or typed slug for "other"
  const [name, setName] = useState(capitalizeFirst(line.name));
  const [category, setCategory] = useState("");

  function emit(next: { kind: Kind; value?: string; name?: string; category?: string }) {
    const k = next.kind;
    if (k === "unset") onChange({ mode: "unset" });
    else if (k === "create") {
      onChange({
        mode: "create",
        name: next.name ?? name,
        category: (next.category ?? category) || null,
      });
    } else onChange({ mode: "map", slug: next.value ?? value });
  }

  return (
    <div className="space-y-2 rounded-md border border-line p-3">
      <label htmlFor={id} className="block text-sm">
        <span className="font-semibold">
          Línea {line.index + 1}: «{line.name}»
        </span>
      </label>
      <select
        id={id}
        className={field}
        value={kind === "candidate" ? `c:${value}` : kind}
        onChange={(event) => {
          const raw = event.target.value;
          if (raw.startsWith("c:")) {
            setKind("candidate");
            setValue(raw.slice(2));
            emit({ kind: "candidate", value: raw.slice(2) });
          } else {
            const next = raw as Kind;
            setKind(next);
            if (next === "other") setValue("");
            emit({ kind: next, value: next === "other" ? "" : value });
          }
        }}
      >
        <option value="unset">Elige qué hacer…</option>
        {line.candidates.map((candidate) => (
          <option key={candidate.slug} value={`c:${candidate.slug}`}>
            Usar «{candidate.name}» (parecido {candidate.similarity})
          </option>
        ))}
        <option value="create">Crear un ingrediente nuevo en el catálogo</option>
        <option value="other">Usar otro ingrediente existente (slug)…</option>
      </select>

      {kind === "create" ? (
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="text-xs text-ink-muted">
            Nombre del ingrediente
            <input
              className={`${field} mt-1 text-ink`}
              value={name}
              maxLength={120}
              onChange={(event) => {
                setName(event.target.value);
                emit({ kind: "create", name: event.target.value });
              }}
            />
          </label>
          <label className="text-xs text-ink-muted">
            Familia
            <select
              className={`${field} mt-1 text-ink`}
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                emit({ kind: "create", category: event.target.value });
              }}
            >
              <option value="">Sin familia</option>
              {categories.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {kind === "other" ? (
        <label className="block text-xs text-ink-muted">
          Slug del ingrediente existente
          <input
            className={`${field} mt-1 text-ink`}
            placeholder="p. ej. chile-jalapeno"
            value={value}
            maxLength={140}
            onChange={(event) => {
              setValue(event.target.value);
              emit({ kind: "other", value: event.target.value });
            }}
          />
        </label>
      ) : null}
    </div>
  );
}
