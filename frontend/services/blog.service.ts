import type {
  BlogPost,
  BlogCategory,
  BlogStage,
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
    return useApi().get<BlogPost>(`/blog/${slug}/`);
  },

  // Crear
  create(payload: BlogFormPayload) {
    return useApi().post<BlogPost>(
      "/blog/",
      toFormData(payload),
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
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
};