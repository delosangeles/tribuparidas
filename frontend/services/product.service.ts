import type { Paginated, Product } from "~/types";
import { toFormData } from "./utils";

export const productService = {
  listByBusinessSlug(slug: string, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Product>>(`/businesses/${slug}/products/`, { params });
  },
  myList(businessId: number) {
    return useApi().get<Paginated<Product> | Product[]>(`/my/businesses/${businessId}/products/`);
  },
  create(businessId: number, payload: Partial<Product> & { image?: File | null }) {
    return useApi().post<Product>(`/my/businesses/${businessId}/products/`, toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  update(productId: number, payload: Partial<Product> & { image?: File | null }) {
    return useApi().patch<Product>(`/my/products/${productId}/`, toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove(productId: number) {
    return useApi().delete(`/my/products/${productId}/`);
  },
};
