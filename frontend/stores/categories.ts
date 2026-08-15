import { defineStore } from "pinia";
import { categoryService } from "~/services/category.service";
import type { Category } from "~/types";

export const useCategoriesStore = defineStore("categories", () => {
  const items = ref<Category[]>([]);
  const loaded = ref(false);
  const loading = ref(false);

  async function fetchAll(force = false) {
    if (loaded.value && !force) return;
    loading.value = true;
    try {
      const { data } = await categoryService.list({ page_size: 50, ordering: "name" });
      items.value = data.results;
      loaded.value = true;
    } finally {
      loading.value = false;
    }
  }

  return { items, loading, loaded, fetchAll };
});
