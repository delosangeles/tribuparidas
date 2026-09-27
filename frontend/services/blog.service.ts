import type {
  BlogPost,
  BlogPostDetail,
  BlogCategory,
  BlogStage,
  BlogComment,
  BlogFormPayload,
  Paginated,
} from "~/types";

import { toFormData } from "./utils";

export const blogService = {
  // Público
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<BlogPost>>("/blog/", { params });
  },

  retrieve(slug: string) {
    return useApi().get<BlogPostDetail>(`/blog/${slug}/`);
  },

  // Crear (cualquier autenticado; queda en revisión salvo que sea admin)
  create(payload: BlogFormPayload) {
    return useApi().post<BlogPostDetail>(
      "/blog/",
      toFormData(payload),
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  },

  // Admin
  update(slug: string, payload: Partial<BlogFormPayload>) {
    return useApi().patch<BlogPostDetail>(
      `/blog/${slug}/`,
      toFormData(payload),
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  },

  remove(slug: string) {
    return useApi().delete(`/blog/${slug}/`);
  },

  approve(slug: string) {
    return useApi().post<BlogPostDetail>(`/blog/${slug}/approve/`);
  },

  reject(slug: string) {
    return useApi().post<BlogPostDetail>(`/blog/${slug}/reject/`);
  },

  // Categorías
  categories(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<BlogCategory>>(
      "/blog/categories/",
      { params }
    );
  },

  // Etapas
  stages(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<BlogStage>>(
      "/blog/stages/",
      { params }
    );
  },

  // Comentarios
  comments(slug: string, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<BlogComment>>(
      `/blog/${slug}/comments/`,
      { params }
    );
  },

  addComment(slug: string, content: string) {
    return useApi().post<BlogComment>(`/blog/${slug}/comments/`, { content });
  },
};