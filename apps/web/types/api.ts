/**
 * Types mirroring the API contract (OpenAPI at /docs on the API).
 * Keep in sync with apps/api/app/schemas.
 *
 * Decimal values (quantities, ratios, ABV) are serialized by the API as strings
 * to avoid floating point loss; they are typed as `DecimalString`.
 */

export type DecimalString = string;
export type RecipeType = "cooking" | "drink";
export type Difficulty = "easy" | "medium" | "hard";
export type SubstitutionType = "equivalent" | "similar" | "emergency";
export type DrinkClassification = "classic" | "variation" | "contemporary" | "experimental";
export type UnitType = "mass" | "volume" | "count" | "other";
export type SourceType = "website" | "book" | "community" | "original" | "ai_generated" | "other";
export type MatchMode = "exact" | "flexible" | "discover";
export type RecipeSort = "relevance" | "newest" | "title" | "quickest";

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  recipe_type: RecipeType;
  recipe_count: number;
}

export interface CategoryRef {
  slug: string;
  name: string;
}

export interface IngredientRef {
  id: string;
  name: string;
  slug: string;
}

export interface Ingredient extends IngredientRef {
  category: CategoryRef | null;
  is_staple: boolean;
  is_alcoholic: boolean;
  recipe_count: number;
}

export interface Unit {
  code: string;
  name: string;
  plural_name: string;
  unit_type: UnitType;
  to_base_factor: DecimalString | null;
}

export interface Alternative {
  ingredient: IngredientRef;
  substitution_type: SubstitutionType;
  ratio: DecimalString;
  notes: string | null;
}

export interface RecipeIngredientRef extends IngredientRef {
  /** Approximate hex color of the ingredient, e.g. "#c8102e". */
  color: string | null;
  is_carbonated: boolean;
}

export interface RecipeIngredient {
  ingredient: RecipeIngredientRef;
  quantity: DecimalString | null;
  quantity_max: DecimalString | null;
  unit: Unit | null;
  is_optional: boolean;
  preparation_notes: string | null;
  group_label: string | null;
  alternatives: Alternative[];
}

export interface Step {
  step_number: number;
  description: string;
  image_url: string | null;
}

export interface Source {
  source_name: string;
  source_url: string | null;
  attribution: string | null;
  license: string | null;
  source_type: SourceType;
}

export interface CatalogItem {
  slug: string;
  name: string;
  description: string | null;
}

export interface RecipeLink {
  slug: string;
  title: string;
}

export interface DrinkDetails {
  is_alcoholic: boolean;
  classification: DrinkClassification;
  base_spirit: IngredientRef | null;
  glass: CatalogItem | null;
  technique: CatalogItem | null;
  garnish: string | null;
  abv_estimate: DecimalString | null;
  variation_of: RecipeLink | null;
  variations: RecipeLink[];
}

export interface RecipeSummary {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  image_url: string | null;
  recipe_type: RecipeType;
  difficulty: Difficulty | null;
  servings: number;
  preparation_time_minutes: number | null;
  cooking_time_minutes: number | null;
  total_time_minutes: number | null;
  categories: CategoryRef[];
  ingredient_count: number;
  is_alcoholic: boolean | null;
  published_at: string | null;
}

export interface Skill {
  slug: string;
  name: string;
  tip: string;
}

export interface RecipePathMembership {
  path_slug: string;
  path_title: string;
  stage_position: number;
  stage_title: string;
}

export interface RecipeDetail extends RecipeSummary {
  introduction: string | null;
  tips: string | null;
  ingredients: RecipeIngredient[];
  steps: Step[];
  sources: Source[];
  drink: DrinkDetails | null;
  related: RecipeSummary[];
  skills: Skill[];
  paths: RecipePathMembership[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Substitution {
  missing: IngredientRef;
  substitute: IngredientRef;
  substitution_type: SubstitutionType;
  ratio: DecimalString;
  notes: string | null;
}

export interface Recommendation {
  recipe: RecipeSummary;
  match_percentage: number;
  available_ingredients: IngredientRef[];
  missing_ingredients: IngredientRef[];
  substitutions: Substitution[];
  assumed_staples: IngredientRef[];
  optional_available: IngredientRef[];
  optional_missing: IngredientRef[];
}

export interface RecommendationsResponse {
  mode: MatchMode;
  assume_staples: boolean;
  ingredients: IngredientRef[];
  unknown_ingredients: string[];
  total: number;
  results: Recommendation[];
}

export interface DishSkill extends Skill {
  /** First dish of the path that teaches this skill. */
  is_new: boolean;
}

export interface PathDish {
  recipe: RecipeSummary;
  skills: DishSkill[];
}

export interface PathStage {
  position: number;
  title: string;
  description: string | null;
  dishes_to_unlock: number;
  dishes: PathDish[];
}

export interface PathSummary {
  slug: string;
  title: string;
  discipline: RecipeType;
  description: string | null;
  stage_count: number;
  dish_count: number;
  skill_count: number;
}

export interface PathDetail extends PathSummary {
  stages: PathStage[];
}

export type UserRole = "user" | "moderator" | "admin";

export interface CurrentUser {
  id: string;
  email: string | null;
  display_name: string;
  role: UserRole;
  created_at: string;
}

export interface DevLoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: CurrentUser;
}

export type IssueSeverity = "error" | "warning" | "info";
export type IngestionStatus =
  "queued" | "running" | "needs_review" | "completed" | "failed" | "rejected";
export type AgentProvider = "opencode" | "claude" | "gemini" | "other";

export interface SubmissionIssue {
  severity: IssueSeverity;
  code: string;
  message: string;
  field_path: string | null;
}

export interface SubmissionLine {
  index: number;
  name: string;
  ingredient_slug: string | null;
  ingredient_name: string | null;
  candidates: { slug: string; name: string; similarity: number }[];
  quantity: DecimalString | null;
  quantity_max: DecimalString | null;
  unit_code: string | null;
  unit_text: string | null;
  optional: boolean;
  notes: string | null;
  group: string | null;
}

export interface PlacementSuggestion {
  path_slug: string;
  path_title: string;
  stage_position: number;
  stage_title: string;
  new_stage: boolean;
  unknown_skills: string[];
  introduces: string[];
  reason: string;
}

export interface DuplicateRef {
  kind: "recipe" | "submission";
  title: string;
  similarity: number;
  reason: string;
  slug: string | null;
  submission_id: string | null;
}

export interface SubmissionAnalysis {
  difficulty: { score: number; label: Difficulty; reasons: string[] };
  skills: { slug: string; name: string }[];
  placements: PlacementSuggestion[];
  duplicates: DuplicateRef[];
  classification: { claimed: DrinkClassification | null; suggested: DrinkClassification } | null;
}

export interface AgentRef {
  id: string;
  name: string;
  provider: string;
}

export interface SubmissionListItem {
  id: string;
  status: IngestionStatus;
  title: string;
  recipe_type: RecipeType;
  agent: AgentRef | null;
  difficulty_score: number | null;
  errors: number;
  warnings: number;
  created_at: string;
}

export interface SubmissionDetail {
  id: string;
  status: IngestionStatus;
  outcome: "created" | "updated" | "unchanged";
  issues: SubmissionIssue[];
  blocking_issues: number;
  analysis: SubmissionAnalysis | null;
  review_notes: string | null;
  recipe_slug: string | null;
  title: string;
  recipe_type: RecipeType;
  source: {
    name: string;
    url: string | null;
    source_type: SourceType;
    license: string | null;
    attribution: string | null;
  };
  description: string | null;
  tips: string | null;
  servings: number;
  preparation_time_minutes: number | null;
  cooking_time_minutes: number | null;
  categories: string[];
  lines: SubmissionLine[];
  steps: string[];
  drink: {
    is_alcoholic: boolean;
    base_spirit: string | null;
    glass: string | null;
    technique: string | null;
    garnish: string | null;
  } | null;
  agent_notes: string | null;
  agent: AgentRef | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface Agent {
  id: string;
  name: string;
  provider: AgentProvider;
  description: string | null;
  token_prefix: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

export interface CreatedAgent extends Agent {
  /** Shown once; only its hash is stored. */
  token: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}
