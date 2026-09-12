import type { News, NewsFormPayload, Paginated } from "~/types";
import { toFormData } from "./utils";

export const newsService = {
  // Público
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<News>>("/news/", { params });
  },

  active() {
    return useApi().get<News[]>("/news/active/");
  },

  retrieve(id: number) {
    return useApi().get<News>(`/news/${id}/`);
  },

  // Admin
  create(payload: NewsFormPayload) {
    return useApi().post<News>(
      "/news/",
      toFormData(payload),
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  },

  update(id: number, payload: Partial<NewsFormPayload>) {
    return useApi().patch<News>(
      `/news/${id}/`,
      toFormData(payload),
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  },

  remove(id: number) {
    return useApi().delete(`/news/${id}/`);
  },
};