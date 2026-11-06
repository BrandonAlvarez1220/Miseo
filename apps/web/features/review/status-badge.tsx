import { Chip } from "@/components/ui/chip";
import type { IngestionStatus } from "@/types/api";

const LABELS: Record<IngestionStatus, { label: string; tone: "neutral" | "primary" | "accent" }> = {
  needs_review: { label: "Por revisar", tone: "accent" },
  completed: { label: "Publicada", tone: "primary" },
  rejected: { label: "Rechazada", tone: "neutral" },
  queued: { label: "En cola", tone: "neutral" },
  running: { label: "Procesando", tone: "neutral" },
  failed: { label: "Fallida", tone: "neutral" },
};

export function StatusBadge({ status }: { status: IngestionStatus }) {
  const { label, tone } = LABELS[status];
  return (
    <Chip tone={tone} size="sm">
      {label}
    </Chip>
  );
}
