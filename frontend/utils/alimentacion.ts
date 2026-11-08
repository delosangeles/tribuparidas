import type { RecipeSummary } from "~/types/alimentacion";

export const MEDICAL_DISCLAIMER =
  "Esta información es orientativa y no reemplaza la consulta con tu pediatra o nutricionista.";

/** Minúsculas y sin tildes: "Plátano" y "platano" se buscan igual. */
export function normalizeSearch(value: string): string {
  return (value || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

export interface RecipeFilters {
  q?: string;
  /** slug del rango de edad */
  age?: string;
  /** slug del tipo de comida */
  mealType?: string;
  /** slugs de alérgenos que NO debe contener la receta */
  withoutAllergens?: string[];
}

/** Filtra en el cliente (búsqueda en tiempo real). Misma lógica que el servidor. */
export function filterRecipes(recipes: RecipeSummary[], filters: RecipeFilters): RecipeSummary[] {
  const words = normalizeSearch(filters.q || "").split(/\s+/).filter(Boolean);
  const excluded = filters.withoutAllergens ?? [];
  return recipes.filter((recipe) => {
    if (filters.age && recipe.age_range.slug !== filters.age) return false;
    if (filters.mealType && recipe.meal_type.slug !== filters.mealType) return false;
    if (excluded.length && recipe.allergens.some((a) => excluded.includes(a.slug))) return false;
    const haystack = recipe.search_text || normalizeSearch(`${recipe.title} ${recipe.summary}`);
    return words.every((word) => haystack.includes(word));
  });
}

export function prepTimeLabel(minutes: number | null | undefined): string {
  if (!minutes) return "";
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}

/** Enlace para compartir una receta por WhatsApp (abre el selector de contactos). */
export function recipeWhatsappUrl(title: string, url: string): string {
  return `https://wa.me/?text=${encodeURIComponent(`${title} — mira esta receta en Tribu Paridas: ${url}`)}`;
}
