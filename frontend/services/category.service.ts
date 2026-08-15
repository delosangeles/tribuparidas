import type { Category, Paginated } from "~/types";
import { toFormData } from "./utils";

export const categoryService = {
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Category>>("/categories/", { params });
  },
  retrieve(slug: string) {
    return useApi().get<Category>(`/categories/${slug}/`);
  },
  create(payload: Partial<Category> & { image?: File | null }) {
    return useApi().post<Category>("/categories/", toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  update(slug: string, payload: Partial<Category> & { image?: File | null }) {
    return useApi().patch<Category>(`/categories/${slug}/`, toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove(slug: string) {
    return useApi().delete(`/categories/${slug}/`);
  },
};
