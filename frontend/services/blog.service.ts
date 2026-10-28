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

  // Imagen para insertar dentro del contenido del artículo
  uploadContentImage(image: File) {
    return useApi().post<{ url: string }>(
      "/blog/upload-image/",
      toFormData({ image }),
      { headers: { "Content-Type": "multipart/form-data" } }
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

  // Comentar o responder (con foto opcional). Con foto viaja como formulario.
  addComment(slug: string, payload: { content: string; image?: File | null; parent?: number | null }) {
    const url = `/blog/${slug}/comments/`;
    if (payload.image) {
      const form = new FormData();
      form.append("content", payload.content);
      form.append("image", payload.image);
      if (payload.parent) form.append("parent", String(payload.parent));
      return useApi().post<BlogComment>(url, form, { headers: { "Content-Type": "multipart/form-data" } });
    }
    return useApi().post<BlogComment>(url, { content: payload.content, ...(payload.parent ? { parent: payload.parent } : {}) });
  },

  // Editar el propio comentario: texto, y foto (cambiarla o quitarla).
  updateComment(slug: string, id: number, payload: { content: string; image?: File | null; removeImage?: boolean }) {
    const url = `/blog/${slug}/comments/${id}/`;
    if (payload.image) {
      const form = new FormData();
      form.append("content", payload.content);
      form.append("image", payload.image);
      return useApi().patch<BlogComment>(url, form, { headers: { "Content-Type": "multipart/form-data" } });
    }
    return useApi().patch<BlogComment>(url, {
      content: payload.content,
      ...(payload.removeImage ? { remove_image: true } : {}),
    });
  },

  deleteComment(slug: string, id: number) {
    return useApi().delete(`/blog/${slug}/comments/${id}/`);
  },

  toggleLike(slug: string, id: number) {
    return useApi().post<{ liked: boolean; like_count: number }>(`/blog/${slug}/comments/${id}/like/`);
  },
};