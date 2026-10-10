import { defineStore } from "pinia";
import { featureFlagService } from "~/services/feature-flag.service";
import type { FeatureFlag } from "~/types";

// Interruptores con activación programada (ver apps/core/models.py
// FeatureFlag): código ya desplegado, oculto hasta la fecha que el Super
// Admin defina en /admin/lanzamiento. Se cargan una vez al iniciar sesión.
export const useFeatureFlagStore = defineStore("featureFlags", () => {
  const flags = ref<Record<string, FeatureFlag>>({});
  const loaded = ref(false);

  async function load() {
    try {
      const { data } = await featureFlagService.list();
      flags.value = Object.fromEntries(data.results.map((flag) => [flag.key, flag]));
    } catch {
      // Si falla, los módulos con lanzamiento programado simplemente quedan
      // ocultos — nunca debe tumbar el login ni el arranque de la app.
    } finally {
      loaded.value = true;
    }
  }

  function isActive(key: string) {
    return Boolean(flags.value[key]?.is_active);
  }

  const isBlogLive = computed(() => isActive("blog_module"));

  const isFestejosLive = computed(() => isActive("festejos_module"));

  return { flags, loaded, load, isActive, isBlogLive, isFestejosLive };
});
