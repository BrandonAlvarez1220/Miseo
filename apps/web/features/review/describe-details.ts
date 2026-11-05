/** Turn the API's structured 422 details into sentences a reviewer can act on. */
export function describeDetails(details: unknown): string[] {
  if (!Array.isArray(details)) return [];
  return details.flatMap((item): string[] => {
    if (typeof item !== "object" || item === null) return [];
    const entry = item as Record<string, unknown>;
    if (typeof entry.line === "number") {
      const what =
        entry.problem === "unit"
          ? `la unidad «${String(entry.text ?? "")}»`
          : `el ingrediente «${String(entry.name ?? "")}»`;
      return [`Línea ${entry.line + 1}: falta resolver ${what}.`];
    }
    if (typeof entry.message === "string") return [entry.message];
    return [];
  });
}
