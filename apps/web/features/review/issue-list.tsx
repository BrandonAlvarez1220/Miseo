import { CircleAlert, Info, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/utils";
import type { IssueSeverity, SubmissionIssue } from "@/types/api";

const STYLE: Record<IssueSeverity, { icon: typeof Info; tone: string; label: string }> = {
  error: { icon: CircleAlert, tone: "bg-danger-soft text-danger", label: "Error" },
  warning: { icon: TriangleAlert, tone: "bg-notice-soft text-notice", label: "Aviso" },
  info: { icon: Info, tone: "bg-surface-muted text-ink-muted", label: "Nota" },
};

/** Spanish titles for the API's issue codes; the API message stays as technical detail. */
export const ISSUE_TITLES: Record<string, string> = {
  unknown_ingredient: "Ingrediente que el catálogo no conoce",
  unknown_unit: "Unidad desconocida",
  missing_quantity: "Falta la cantidad",
  missing_unit: "Falta la unidad",
  implausible_quantity: "Cantidad sospechosamente grande",
  unknown_category: "Categoría inexistente",
  no_category: "Sin categoría válida",
  unknown_glass: "Copa desconocida",
  unknown_technique: "Técnica desconocida",
  possible_duplicate: "Posible duplicado",
  license_unknown: "Licencia no indicada",
  missing_time: "Sin tiempos",
  short_steps: "Pasos muy escuetos",
  classification_downgraded: "Clasificación rebajada a experimental",
};

export function issueTitle(code: string): string {
  return ISSUE_TITLES[code] ?? code;
}

export function IssueList({ issues }: { issues: SubmissionIssue[] }) {
  if (issues.length === 0) {
    return <p className="text-sm text-ink-muted">Sin problemas detectados.</p>;
  }
  return (
    <ul className="space-y-2">
      {issues.map((issue, index) => {
        const { icon: Icon, tone, label } = STYLE[issue.severity];
        return (
          <li
            key={`${issue.code}-${index}`}
            className={cn("flex gap-2 rounded-md px-3 py-2 text-sm", tone)}
          >
            <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            <span>
              <span className="sr-only">{label}: </span>
              <span className="font-semibold">{issueTitle(issue.code)}</span>
              <span className="block text-xs opacity-80">{issue.message}</span>
            </span>
          </li>
        );
      })}
    </ul>
  );
}
