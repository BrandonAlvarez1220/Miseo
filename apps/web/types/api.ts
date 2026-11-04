/**
 * Types mirroring the API contract (see the OpenAPI spec at /docs on the API).
 * Keep in sync with apps/api/app/schemas.
 */

export type RecipeType = "cooking" | "drink";

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  recipe_type: RecipeType;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}
