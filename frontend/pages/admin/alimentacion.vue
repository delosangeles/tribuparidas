<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { CatalogItem } from "~/types/alimentacion";

definePageMeta({ layout: "admin", middleware: "admin", module: "alimentacion" });

const TABS = [
  { key: "recetas", label: "Recetas" },
  { key: "guias", label: "Guías" },
  { key: "alimentos", label: "Alimentos" },
  { key: "seguridad", label: "Seguridad" },
  { key: "catalogos", label: "Catálogos" },
] as const;
const tab = ref<(typeof TABS)[number]["key"]>("recetas");

// Catálogos (edades, tipos y alérgenos): los usan los formularios de recetas y alimentos.
const ages = ref<CatalogItem[]>([]);
const mealTypes = ref<CatalogItem[]>([]);
const allergens = ref<CatalogItem[]>([]);
const ready = ref(false);
async function loadCatalogs() {
  const api = alimentacionService.admin;
  [ages.value, mealTypes.value, allergens.value] = (
    await Promise.all([api.list<CatalogItem>("edades"), api.list<CatalogItem>("tipos"), api.list<CatalogItem>("alergenos")])
  ).map((r) => r.data);
  ready.value = true;
}
await loadCatalogs();

const flags = useFeatureFlagStore();
</script>

<template>
  <div class="space-y-6 p-4 sm:p-6">
    <header class="space-y-1">
      <h1 class="font-display text-2xl text-ink">Alimentación complementaria</h1>
      <p class="text-sm text-muted">
        Todo se crea como borrador. Revisa con «Vista previa» y publica solo contenido validado por un profesional.
      </p>
      <p v-if="!flags.isAlimentacionLive" class="rounded-xl2 bg-gold-light/50 px-3 py-2 text-sm text-gold-dark">
        El módulo aún no está lanzado: las usuarias no lo ven. Se programa en Admin → Lanzamiento.
      </p>
    </header>

    <nav class="flex gap-1 overflow-x-auto border-b border-line">
      <button
        v-for="item in TABS" :key="item.key" type="button"
        class="whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-semibold transition"
        :class="tab === item.key ? 'border-gold text-gold-dark' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </nav>

    <RecipesAdmin v-if="tab === 'recetas' && ready" :ages="ages" :meal-types="mealTypes" :allergens="allergens" />
    <GuidesAdmin v-else-if="tab === 'guias'" />
    <FoodsAdmin v-else-if="tab === 'alimentos' && ready" :ages="ages" :allergens="allergens" />
    <SafetyAdmin v-else-if="tab === 'seguridad'" />
    <CatalogsAdmin v-else-if="tab === 'catalogos'" @changed="loadCatalogs" />
  </div>
</template>
