<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { RecipeSummary } from "~/types/alimentacion";

// Ruta privada (utils/routePath.ts): el middleware global pide sesión.
definePageMeta({ middleware: "alimentacion" });

useHead({ title: "Mis recetas favoritas | Tribu Paridas", meta: [{ name: "robots", content: "noindex" }] });

const recipes = ref<RecipeSummary[]>([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    recipes.value = (await alimentacionService.favorites()).data;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
});

// Al quitar el corazón la receta sale de la lista.
function onFavorite(recipe: RecipeSummary, value: boolean) {
  if (!value) recipes.value = recipes.value.filter((r) => r.id !== recipe.id);
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
    <NuxtLink to="/alimentacion-complementaria" class="inline-flex items-center gap-1 text-sm text-muted hover:text-gold">
      <AppIcon name="arrow" :size="14" class="rotate-180" /> Volver a recetas
    </NuxtLink>
    <h1 class="font-display text-3xl text-ink">Mis recetas favoritas</h1>
    <MedicalDisclaimer />

    <LoadingSpinner v-if="loading" />
    <p v-else-if="error" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">{{ error }}</p>
    <div v-else-if="recipes.length" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      <RecipeCard v-for="recipe in recipes" :key="recipe.id" :recipe="recipe" @favorite="onFavorite(recipe, $event)" />
    </div>
    <EmptyState v-else icon="heart" title="Aún no guardas recetas" description="Toca el corazón en una receta para encontrarla aquí." />
  </div>
</template>
