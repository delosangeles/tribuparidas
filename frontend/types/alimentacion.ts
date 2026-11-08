export type AlimentacionStatus = "draft" | "published";

export interface CatalogRef {
  id: number;
  name: string;
  slug: string;
}

export interface CatalogItem extends CatalogRef {
  order: number;
  is_active: boolean;
}

export interface Catalogs {
  ages: CatalogItem[];
  meal_types: CatalogItem[];
  allergens: CatalogItem[];
}

export interface RecipeSummary {
  id: number;
  slug: string;
  title: string;
  summary: string;
  image: string | null;
  age_range: CatalogRef;
  meal_type: CatalogRef;
  prep_time_minutes: number | null;
  allergens: CatalogRef[];
  /** Título + resumen + ingredientes, sin tildes: lo usa el buscador. */
  search_text: string;
  is_favorite: boolean;
  status: AlimentacionStatus;
}

export interface RecipeDetail extends RecipeSummary {
  storage_tip: string;
  ingredients: { name: string; quantity: string }[];
  steps: { text: string }[];
  updated_at: string;
}

export interface GuideSummary {
  id: number;
  slug: string;
  title: string;
  summary: string;
  image: string | null;
  updated_at: string;
}

export interface GuideDetail extends GuideSummary {
  content: string;
  status: AlimentacionStatus;
}

export interface FoodItem {
  id: number;
  slug: string;
  name: string;
  age_range: CatalogRef | null;
  how_to_offer: string;
  is_common_allergen: boolean;
  allergen: CatalogRef | null;
  status: AlimentacionStatus;
}

export type SafetyContent =
  | { published: false }
  | {
      published: true;
      content: string;
      professional_name: string;
      professional_title: string;
      reviewed_on: string | null;
      status: AlimentacionStatus;
      updated_at: string;
    };

// ---- Panel admin (los campos relacionados van como ids)
export interface RecipeAdmin {
  id: number;
  slug: string;
  title: string;
  summary: string;
  image: string | null;
  age_range: number;
  meal_type: number;
  prep_time_minutes: number | null;
  allergens: number[];
  storage_tip: string;
  ingredients: { name: string; quantity: string }[];
  steps: { text: string }[];
  order: number;
  status: AlimentacionStatus;
  updated_at: string;
}

export interface GuideAdmin {
  id: number;
  slug: string;
  title: string;
  summary: string;
  content: string;
  image: string | null;
  order: number;
  status: AlimentacionStatus;
  updated_at: string;
}

export interface FoodAdmin {
  id: number;
  slug: string;
  name: string;
  age_range: number | null;
  how_to_offer: string;
  is_common_allergen: boolean;
  allergen: number | null;
  order: number;
  status: AlimentacionStatus;
}

export interface SafetyAdmin {
  content: string;
  professional_name: string;
  professional_title: string;
  reviewed_on: string | null;
  status: AlimentacionStatus;
}
