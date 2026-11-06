import { apiFetch } from "@/lib/api-client";
import type {
  CatalogItem,
  Category,
  IngestionStatus,
  Page,
  SubmissionDetail,
  SubmissionListItem,
  Unit,
} from "@/types/api";

export interface ApprovePayload {
  ingredient_mappings: Record<string, string>;
  new_ingredients: Record<string, { name: string; category: string | null }>;
  unit_mappings: Record<string, string>;
  categories: string[];
  classification?: string;
  difficulty?: string;
  skills: string[];
  placement: { path_slug: string; stage_position: number } | null;
  review_notes: string | null;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

export function listSubmissions(
  token: string,
  query: { status: IngestionStatus; page?: number },
): Promise<Page<SubmissionListItem>> {
  return apiFetch<Page<SubmissionListItem>>("/api/v1/review/submissions", {
    token,
    query: { status: query.status, page: query.page },
  });
}

export function getSubmission(token: string, id: string): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(`/api/v1/review/submissions/${encodeURIComponent(id)}`, {
    token,
  });
}

export function approveSubmission(
  token: string,
  id: string,
  body: ApprovePayload,
): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(
    `/api/v1/review/submissions/${encodeURIComponent(id)}/approve`,
    {
      token,
      init: { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) },
    },
  );
}

export function rejectSubmission(
  token: string,
  id: string,
  reviewNotes: string,
): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(`/api/v1/review/submissions/${encodeURIComponent(id)}/reject`, {
    token,
    init: {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({ review_notes: reviewNotes }),
    },
  });
}

export interface ReviewCatalogs {
  units: Unit[];
  ingredientCategories: { slug: string; name: string }[];
  categories: Category[];
}

export async function loadReviewCatalogs(recipeType: "cooking" | "drink"): Promise<ReviewCatalogs> {
  const [units, ingredientCategories, categories] = await Promise.all([
    apiFetch<Unit[]>("/api/v1/units"),
    apiFetch<{ slug: string; name: string }[]>("/api/v1/ingredients/categories"),
    apiFetch<Category[]>("/api/v1/categories", { query: { recipe_type: recipeType } }),
  ]);
  return { units, ingredientCategories, categories };
}

export type { CatalogItem };
