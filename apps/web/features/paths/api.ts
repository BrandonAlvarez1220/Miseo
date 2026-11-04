import { apiFetch } from "@/lib/api-client";
import type { PathDetail, PathSummary } from "@/types/api";

export function listPaths(): Promise<PathSummary[]> {
  return apiFetch<PathSummary[]>("/api/v1/paths");
}

export function getPath(slug: string): Promise<PathDetail> {
  return apiFetch<PathDetail>(`/api/v1/paths/${encodeURIComponent(slug)}`);
}
