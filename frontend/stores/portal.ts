import { defineStore } from "pinia";
import { portalService } from "~/services/portal.service";
import type { PortalBusinessRef } from "~/types";

// Emprendimientos a los que la persona tiene acceso en el portal y cuál está
// viendo ahora. La propiedad se vuelve a verificar en el servidor en cada petición.
export const usePortalStore = defineStore("portal", () => {
  const businesses = ref<PortalBusinessRef[]>([]);
  const currentId = ref<number | null>(null);
  const loaded = ref(false);

  async function load() {
    const { data } = await portalService.mine();
    businesses.value = data;
    if (!data.some((b) => b.business_id === currentId.value)) currentId.value = data[0]?.business_id ?? null;
    loaded.value = true;
  }

  function select(id: number) {
    if (businesses.value.some((b) => b.business_id === id)) currentId.value = id;
  }

  const current = computed(() => businesses.value.find((b) => b.business_id === currentId.value) ?? null);
  const isOwner = computed(() => current.value?.role === "owner");

  function reset() {
    businesses.value = [];
    currentId.value = null;
    loaded.value = false;
  }

  return { businesses, currentId, loaded, current, isOwner, load, select, reset };
});
