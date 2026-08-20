import type { Business, BusinessFormPayload, BusinessImage, Paginated } from "~/types";
import { toFormData } from "./utils";

export const businessService = {
  // Público
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Business>>("/businesses/", { params });
  },
  retrieve(slug: string) {
    return useApi().get<Business>(`/businesses/${slug}/`);
  },

  // Propios (emprendedor)
  myList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Business>>("/my/businesses/", { params });
  },
  myRetrieve(id: number) {
    return useApi().get<Business>(`/my/businesses/${id}/`);
  },
  create(payload: BusinessFormPayload) {
    return useApi().post<Business>("/my/businesses/", toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  update(id: number, payload: Partial<BusinessFormPayload>) {
    return useApi().patch<Business>(`/my/businesses/${id}/`, toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove(id: number) {
    return useApi().delete(`/my/businesses/${id}/`);
  },

  // Galería
  listImages(businessId: number) {
    return useApi().get<Paginated<BusinessImage> | BusinessImage[]>(`/my/businesses/${businessId}/images/`);
  },
  uploadImage(businessId: number, image: File, caption = "", order = 0) {
    return useApi().post<BusinessImage>(
      `/my/businesses/${businessId}/images/`,
      toFormData({ image, caption, order }),
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },
  removeImage(businessId: number, imageId: number) {
    return useApi().delete(`/my/businesses/${businessId}/images/${imageId}/`);
  },

  // Admin
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Business>>("/admin/businesses/", { params });
  },
  adminRetrieve(id: number) {
    return useApi().get<Business>(`/admin/businesses/${id}/`);
  },
  approve(id: number) {
    return useApi().patch<Business>(`/admin/businesses/${id}/approve/`);
  },
  reject(id: number) {
    return useApi().patch<Business>(`/admin/businesses/${id}/reject/`);
  },
  adminCreate(payload: BusinessFormPayload & { status?: string }) {
    return useApi().post<Business>("/admin/businesses/", toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  adminUpdate(id: number, payload: Partial<BusinessFormPayload> & { status?: string }) {
    return useApi().patch<Business>(`/admin/businesses/${id}/`, toFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
