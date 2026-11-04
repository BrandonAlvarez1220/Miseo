import type { Difficulty, DrinkClassification, SubstitutionType } from "@/types/api";

export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  easy: "Fácil",
  medium: "Media",
  hard: "Difícil",
};

export const SUBSTITUTION_LABELS: Record<SubstitutionType, string> = {
  equivalent: "equivalente",
  similar: "similar",
  emergency: "de emergencia",
};

export const CLASSIFICATION_LABELS: Record<DrinkClassification, string> = {
  classic: "Clásico",
  variation: "Variación",
  contemporary: "Contemporáneo",
  experimental: "Experimental",
};

/** 75 -> "1 h 15 min"; 45 -> "45 min"; null -> null. */
export function formatMinutes(minutes: number | null | undefined): string | null {
  if (minutes === null || minutes === undefined) return null;
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

export function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}
