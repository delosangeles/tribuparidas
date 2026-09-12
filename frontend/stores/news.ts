import { defineStore } from "pinia";
import { newsService } from "~/services/news.service";
import type { News, NewsFormPayload } from "~/types";

export const useNewsStore = defineStore("news", () => {
  const news = ref<News[]>([]);
  const activeNews = ref<News[]>([]);
  const loading = ref(false);

  async function fetchNews() {
    loading.value = true;

    try {
      const { data } = await newsService.list({ page_size: 50 });
      news.value = data.results;
    } finally {
      loading.value = false;
    }
  }

  async function fetchActiveNews() {
    loading.value = true;

    try {
      const { data } = await newsService.active();
      activeNews.value = data;
    } finally {
      loading.value = false;
    }
  }

  async function createNews(payload: NewsFormPayload) {
    const { data } = await newsService.create(payload);

    news.value = [data, ...news.value];

    return data;
  }

  async function updateNews(
    id: number,
    payload: Partial<NewsFormPayload>
  ) {
    const { data } = await newsService.update(id, payload);

    news.value = news.value.map((item) =>
      item.id === id ? data : item
    );

    activeNews.value = activeNews.value.map((item) =>
      item.id === id ? data : item
    );

    return data;
  }

  async function removeNews(id: number) {
    await newsService.remove(id);

    news.value = news.value.filter((item) => item.id !== id);

    activeNews.value = activeNews.value.filter(
      (item) => item.id !== id
    );
  }

  return {
    news,
    activeNews,
    loading,
    fetchNews,
    fetchActiveNews,
    createNews,
    updateNews,
    removeNews,
  };
});