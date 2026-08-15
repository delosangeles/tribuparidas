import { defineStore } from "pinia";
import { businessService } from "~/services/business.service";
import type { Business, BusinessFormPayload } from "~/types";

export const useBusinessStore = defineStore("business", () => {
  const myBusinesses = ref<Business[]>([]);
  const loading = ref(false);

  const primaryBusiness = computed(() => myBusinesses.value[0] || null);

  async function fetchMyBusinesses() {
    loading.value = true;
    try {
      const { data } = await businessService.myList({ page_size: 50 });
      myBusinesses.value = data.results;
    } finally {
      loading.value = false;
    }
  }

  async function createBusiness(payload: BusinessFormPayload) {
    const { data } = await businessService.create(payload);
    myBusinesses.value = [data, ...myBusinesses.value];
    return data;
  }

  async function updateBusiness(id: number, payload: Partial<BusinessFormPayload>) {
    const { data } = await businessService.update(id, payload);
    myBusinesses.value = myBusinesses.value.map((b) => (b.id === id ? data : b));
    return data;
  }

  return { myBusinesses, loading, primaryBusiness, fetchMyBusinesses, createBusiness, updateBusiness };
});
