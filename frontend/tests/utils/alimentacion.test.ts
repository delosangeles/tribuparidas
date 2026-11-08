import { describe, expect, it } from "vitest";
import { filterRecipes, normalizeSearch, prepTimeLabel, recipeWhatsappUrl } from "~/utils/alimentacion";
import type { RecipeSummary } from "~/types/alimentacion";

const ref = (id: number, name: string) => ({ id, name, slug: normalizeSearch(name).replace(/\s+/g, "-") });

function recipe(id: number, title: string, opts: Partial<RecipeSummary> & { ingredients?: string } = {}): RecipeSummary {
  return {
    id,
    slug: `r-${id}`,
    title,
    summary: "",
    image: null,
    age_range: ref(1, "6-8 meses"),
    meal_type: ref(1, "Puré"),
    prep_time_minutes: null,
    allergens: [],
    search_text: normalizeSearch(`${title} ${opts.ingredients ?? ""}`),
    is_favorite: false,
    status: "published",
    ...opts,
  };
}

const huevo = ref(1, "Huevo");
const mani = ref(2, "Maní");

const list = [
  recipe(1, "Crema de calabaza", { ingredients: "Plátano" }),
  recipe(2, "Tortilla suave", { age_range: ref(2, "9-11 meses"), meal_type: ref(2, "Desayuno"), allergens: [huevo] }),
  recipe(3, "Galletas de avena", { age_range: ref(2, "9-11 meses"), meal_type: ref(3, "Snack"), allergens: [huevo, mani] }),
];

describe("normalizeSearch", () => {
  it("quita tildes y mayúsculas", () => {
    expect(normalizeSearch("  PLÁTANO Maní ")).toBe("platano mani");
    expect(normalizeSearch("")).toBe("");
  });
});

describe("filterRecipes", () => {
  it("sin filtros devuelve todo", () => {
    expect(filterRecipes(list, {})).toHaveLength(3);
  });

  it("busca sin distinguir tildes ni mayúsculas, también por ingrediente", () => {
    expect(filterRecipes(list, { q: "PLATANO" }).map((r) => r.id)).toEqual([1]);
    expect(filterRecipes(list, { q: "plátano" }).map((r) => r.id)).toEqual([1]);
    expect(filterRecipes(list, { q: "tortilla" }).map((r) => r.id)).toEqual([2]);
  });

  it("todas las palabras deben coincidir, en cualquier orden", () => {
    expect(filterRecipes(list, { q: "avena galletas" }).map((r) => r.id)).toEqual([3]);
    expect(filterRecipes(list, { q: "avena calabaza" })).toEqual([]);
  });

  it("filtra por edad y por tipo de comida", () => {
    expect(filterRecipes(list, { age: list[1].age_range.slug }).map((r) => r.id)).toEqual([2, 3]);
    expect(filterRecipes(list, { mealType: list[2].meal_type.slug }).map((r) => r.id)).toEqual([3]);
  });

  it("excluye las recetas que contienen los alérgenos elegidos", () => {
    expect(filterRecipes(list, { withoutAllergens: [huevo.slug] }).map((r) => r.id)).toEqual([1]);
    expect(filterRecipes(list, { withoutAllergens: [mani.slug] }).map((r) => r.id)).toEqual([1, 2]);
  });

  it("combina búsqueda y filtros", () => {
    expect(filterRecipes(list, { q: "galletas", age: list[1].age_range.slug, withoutAllergens: [mani.slug] })).toEqual([]);
    expect(filterRecipes(list, { q: "tortilla", age: list[1].age_range.slug }).map((r) => r.id)).toEqual([2]);
  });
});

describe("prepTimeLabel", () => {
  it("formatea minutos y horas", () => {
    expect(prepTimeLabel(null)).toBe("");
    expect(prepTimeLabel(25)).toBe("25 min");
    expect(prepTimeLabel(60)).toBe("1 h");
    expect(prepTimeLabel(90)).toBe("1 h 30 min");
  });
});

describe("recipeWhatsappUrl", () => {
  it("arma un enlace de WhatsApp con el título y la URL codificados", () => {
    const url = recipeWhatsappUrl("Puré de ejemplo", "https://sitio.test/alimentacion-complementaria/pure?x=1&y=2");
    expect(url.startsWith("https://wa.me/?text=")).toBe(true);
    const text = decodeURIComponent(url.split("text=")[1]);
    expect(text).toContain("Puré de ejemplo");
    expect(text).toContain("https://sitio.test/alimentacion-complementaria/pure?x=1&y=2");
  });
});
