import { apiFetch } from "@/lib/api-client";
import type { CatalogItem } from "@/types/api";

export function listTechniques(): Promise<CatalogItem[]> {
  return apiFetch<CatalogItem[]>("/api/v1/mixology/techniques");
}

export function listGlassTypes(): Promise<CatalogItem[]> {
  return apiFetch<CatalogItem[]>("/api/v1/mixology/glass-types");
}
