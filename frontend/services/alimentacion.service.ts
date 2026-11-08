import type {
  Catalogs,
  FoodAdmin,
  FoodItem,
  GuideAdmin,
  GuideDetail,
  GuideSummary,
  RecipeAdmin,
  RecipeDetail,
  RecipeSummary,
  SafetyAdmin,
  SafetyContent,
} from "~/types/alimentacion";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };
const preview = (on?: boolean) => (on ? { preview: 1 } : undefined);

export const alimentacionService = {
  // ---- público
  catalogs: () => useApi().get<Catalogs>("/alimentacion/catalogos/"),
  recipes: (params?: Record<string, string>) => useApi().get<RecipeSummary[]>("/alimentacion/recetas/", { params }),
  recipe: (slug: string, previewMode?: boolean) =>
    useApi().get<RecipeDetail>(`/alimentacion/recetas/${slug}/`, { params: preview(previewMode) }),
  guides: (previewMode?: boolean) => useApi().get<GuideSummary[]>("/alimentacion/guias/", { params: preview(previewMode) }),
  guide: (slug: string, previewMode?: boolean) =>
    useApi().get<GuideDetail>(`/alimentacion/guias/${slug}/`, { params: preview(previewMode) }),
  foods: (previewMode?: boolean) => useApi().get<FoodItem[]>("/alimentacion/alimentos/", { params: preview(previewMode) }),
  safety: (previewMode?: boolean) => useApi().get<SafetyContent>("/alimentacion/seguridad/", { params: preview(previewMode) }),
  favorites: () => useApi().get<RecipeSummary[]>("/alimentacion/favoritos/"),
  addFavorite: (slug: string) => useApi().post(`/alimentacion/recetas/${slug}/favorito/`),
  removeFavorite: (slug: string) => useApi().delete(`/alimentacion/recetas/${slug}/favorito/`),

  // ---- panel admin
  admin: {
    list: <T>(kind: string, params?: Record<string, string>) => useApi().get<T[]>(`/alimentacion/admin/${kind}/`, { params }),
    create: <T>(kind: string, payload: object) => useApi().post<T>(`/alimentacion/admin/${kind}/`, payload),
    update: <T>(kind: string, id: number, payload: object) => useApi().patch<T>(`/alimentacion/admin/${kind}/${id}/`, payload),
    remove: (kind: string, id: number) => useApi().delete(`/alimentacion/admin/${kind}/${id}/`),
    publish: <T>(kind: string, id: number) => useApi().post<T>(`/alimentacion/admin/${kind}/${id}/publish/`),
    unpublish: <T>(kind: string, id: number) => useApi().post<T>(`/alimentacion/admin/${kind}/${id}/unpublish/`),
    reorder: (kind: string, ids: number[]) => useApi().post(`/alimentacion/admin/${kind}/reorder/`, { ids }),
    uploadImage: <T>(kind: string, id: number, file: File) => {
      const form = new FormData();
      form.append("image", file);
      return useApi().post<T>(`/alimentacion/admin/${kind}/${id}/image/`, form, MULTIPART);
    },
    removeImage: <T>(kind: string, id: number) => useApi().delete<T>(`/alimentacion/admin/${kind}/${id}/image/`),
    recipes: (params?: Record<string, string>) => useApi().get<RecipeAdmin[]>("/alimentacion/admin/recetas/", { params }),
    guides: () => useApi().get<GuideAdmin[]>("/alimentacion/admin/guias/"),
    foods: () => useApi().get<FoodAdmin[]>("/alimentacion/admin/alimentos/"),
    safety: () => useApi().get<SafetyAdmin>("/alimentacion/admin/seguridad/"),
    saveSafety: (payload: Partial<SafetyAdmin>) => useApi().patch<SafetyAdmin>("/alimentacion/admin/seguridad/", payload),
  },
};
