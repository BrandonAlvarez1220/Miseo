import { ExternalLink } from "lucide-react";
import Link from "next/link";

import { DIFFICULTY_LABELS, formatMinutes } from "@/lib/format";
import { parseDecimal } from "@/lib/quantity";
import type { SubmissionDetail } from "@/types/api";

import { IssueList } from "./issue-list";

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-line bg-surface p-5">
      <h2 className="mb-3 text-lg font-bold">{title}</h2>
      {children}
    </section>
  );
}

function quantityText(line: SubmissionDetail["lines"][number]): string {
  const quantity = parseDecimal(line.quantity);
  if (quantity === null) return line.unit_text ?? "—";
  const max = parseDecimal(line.quantity_max);
  const amount = max !== null ? `${quantity}–${max}` : `${quantity}`;
  return `${amount} ${line.unit_code ?? line.unit_text ?? ""}`.trim();
}

/** Read-only view of what the agent sent and what the pipeline found. */
export function SubmissionSummary({ detail }: { detail: SubmissionDetail }) {
  const { source, analysis } = detail;
  return (
    <div className="space-y-5">
      <Block title="Fuente y procedencia">
        <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-ink-muted">Fuente</dt>
            <dd className="font-medium">{source.name}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">Tipo</dt>
            <dd>{source.source_type}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">Enlace</dt>
            <dd>
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer nofollow"
                  className="inline-flex items-center gap-1 break-all text-primary hover:underline"
                >
                  {source.url}
                  <ExternalLink aria-hidden="true" className="size-3.5 shrink-0" />
                </a>
              ) : (
                "—"
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">Licencia</dt>
            <dd>{source.license ?? <span className="text-notice">no indicada</span>}</dd>
          </div>
          {source.attribution ? (
            <div className="sm:col-span-2">
              <dt className="text-xs text-ink-muted">Atribución</dt>
              <dd>{source.attribution}</dd>
            </div>
          ) : null}
          {detail.agent ? (
            <div className="sm:col-span-2">
              <dt className="text-xs text-ink-muted">Enviada por</dt>
              <dd>
                {detail.agent.name}{" "}
                <span className="text-ink-muted">({detail.agent.provider})</span>
              </dd>
            </div>
          ) : null}
        </dl>
        {detail.agent_notes ? (
          <p className="mt-3 rounded-md bg-surface-muted px-3 py-2 text-sm">
            <span className="font-semibold">Nota del agente:</span> {detail.agent_notes}
          </p>
        ) : null}
      </Block>

      <Block title="Problemas detectados">
        <IssueList issues={detail.issues} />
      </Block>

      {analysis ? (
        <Block title="Análisis automático">
          <div className="space-y-3 text-sm">
            <p>
              <span className="font-semibold">Dificultad:</span> {analysis.difficulty.score}/5 (
              {DIFFICULTY_LABELS[analysis.difficulty.label]}){" "}
              <span className="text-ink-muted">— {analysis.difficulty.reasons.join(" · ")}</span>
            </p>
            {analysis.skills.length ? (
              <p>
                <span className="font-semibold">Habilidades sugeridas:</span>{" "}
                {analysis.skills.map((skill) => skill.name).join(", ")}
              </p>
            ) : null}
            {analysis.duplicates.length ? (
              <div>
                <p className="font-semibold">Posibles duplicados</p>
                <ul className="mt-1 list-inside list-disc text-ink-muted">
                  {analysis.duplicates.map((duplicate) => (
                    <li key={`${duplicate.kind}-${duplicate.slug ?? duplicate.submission_id}`}>
                      {duplicate.slug ? (
                        <Link
                          href={`/recetas/${duplicate.slug}`}
                          className="text-primary hover:underline"
                        >
                          {duplicate.title}
                        </Link>
                      ) : duplicate.submission_id ? (
                        <Link
                          href={`/revision/${duplicate.submission_id}`}
                          className="text-primary hover:underline"
                        >
                          {duplicate.title} (envío pendiente)
                        </Link>
                      ) : (
                        duplicate.title
                      )}{" "}
                      · {duplicate.reason} ({duplicate.similarity})
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </Block>
      ) : null}

      <Block title="Receta">
        <p className="text-sm text-ink-muted">
          {detail.servings} porciones
          {formatMinutes(detail.preparation_time_minutes)
            ? ` · preparación ${formatMinutes(detail.preparation_time_minutes)}`
            : ""}
          {formatMinutes(detail.cooking_time_minutes)
            ? ` · cocción ${formatMinutes(detail.cooking_time_minutes)}`
            : ""}
        </p>
        {detail.description ? <p className="mt-2">{detail.description}</p> : null}
        {detail.drink ? (
          <p className="mt-2 text-sm text-ink-muted">
            {detail.drink.is_alcoholic ? "Con alcohol" : "Sin alcohol"}
            {detail.drink.glass ? ` · copa: ${detail.drink.glass}` : ""}
            {detail.drink.technique ? ` · técnica: ${detail.drink.technique}` : ""}
            {detail.drink.garnish ? ` · guarnición: ${detail.drink.garnish}` : ""}
          </p>
        ) : null}

        <h3 className="mt-4 mb-2 text-sm font-semibold">Ingredientes</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[28rem] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-ink-muted">
                <th scope="col" className="py-2 pr-3 font-medium">
                  Línea
                </th>
                <th scope="col" className="py-2 pr-3 font-medium">
                  Escrito por el agente
                </th>
                <th scope="col" className="py-2 pr-3 font-medium">
                  Cantidad
                </th>
                <th scope="col" className="py-2 font-medium">
                  En el catálogo
                </th>
              </tr>
            </thead>
            <tbody>
              {detail.lines.map((line) => (
                <tr key={line.index} className="border-b border-line last:border-0">
                  <td className="py-2 pr-3 text-ink-muted">{line.index + 1}</td>
                  <td className="py-2 pr-3">
                    {line.name}
                    {line.optional ? <span className="text-ink-muted"> (opcional)</span> : null}
                    {line.notes ? <span className="text-ink-muted">, {line.notes}</span> : null}
                  </td>
                  <td className="py-2 pr-3">{quantityText(line)}</td>
                  <td className="py-2">
                    {line.ingredient_name ?? (
                      <span className="font-semibold text-danger">sin coincidencia</span>
                    )}
                    {line.unit_text && !line.unit_code ? (
                      <span className="block text-xs text-danger">
                        unidad «{line.unit_text}» desconocida
                      </span>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className="mt-4 mb-2 text-sm font-semibold">Pasos</h3>
        <ol className="list-inside list-decimal space-y-1 text-sm">
          {detail.steps.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
        {detail.tips ? (
          <p className="mt-3 text-sm">
            <span className="font-semibold">Consejo:</span> {detail.tips}
          </p>
        ) : null}
      </Block>
    </div>
  );
}
