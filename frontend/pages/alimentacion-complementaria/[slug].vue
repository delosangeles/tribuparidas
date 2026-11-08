<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { RecipeDetail } from "~/types/alimentacion";
import { prepTimeLabel, recipeWhatsappUrl } from "~/utils/alimentacion";

definePageMeta({ middleware: "alimentacion" });

const route = useRoute();
const authStore = useAuthStore();
const slug = route.params.slug as string;
const preview = route.query.preview === "1" && authStore.hasModule("alimentacion");

const recipe = ref<RecipeDetail | null>(null);
const loading = ref(true);
const notFound = ref(false);
const error = ref("");

try {
  recipe.value = (await alimentacionService.recipe(slug, preview)).data;
} catch (err: any) {
  if (err?.response?.status === 404) notFound.value = true;
  else error.value = useErrorMessage(err);
} finally {
  loading.value = false;
}

const r = recipe.value;
const { canonical } = usePageSeo({
  title: r ? r.title : "Receta no encontrada",
  description: r ? r.summary || `Receta para bebés de ${r.age_range.name}: ${r.title}.` : "",
  path: `/alimentacion-complementaria/${slug}`,
  image: r?.image,
});
if (!r) useHead({ meta: [{ name: "robots", content: "noindex" }] });

const whatsappUrl = computed(() => (recipe.value ? recipeWhatsappUrl(recipe.value.title, canonical) : ""));
const favorite = computed({
  get: () => recipe.value?.is_favorite ?? false,
  set: (value: boolean) => {
    if (recipe.value) recipe.value.is_favorite = value;
  },
});
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
    <NuxtLink to="/alimentacion-complementaria" class="inline-flex items-center gap-1 text-sm text-muted hover:text-gold">
      <AppIcon name="arrow" :size="14" class="rotate-180" /> Volver a recetas
    </NuxtLink>

    <MedicalDisclaimer />

    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="notFound" icon="leaf" title="No encontramos esta receta" />
    <p v-else-if="error" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">{{ error }}</p>

    <article v-else-if="recipe" class="space-y-6">
      <p v-if="recipe.status === 'draft'" class="rounded-xl2 bg-ink px-4 py-2 text-sm text-white">
        Vista previa: esta receta es un borrador y las usuarias todavía no la ven.
      </p>

      <img v-if="recipe.image" :src="recipe.image" :alt="recipe.title" class="aspect-[4/3] w-full rounded-xl2 object-cover shadow-soft" />

      <header class="space-y-3">
        <h1 class="font-display text-3xl text-ink sm:text-4xl">{{ recipe.title }}</h1>
        <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
          <span class="badge bg-gold-light text-gold-dark">{{ recipe.age_range.name }}</span>
          <span>{{ recipe.meal_type.name }}</span>
          <span v-if="recipe.prep_time_minutes" class="flex items-center gap-1">
            <AppIcon name="clock" :size="14" /> {{ prepTimeLabel(recipe.prep_time_minutes) }}
          </span>
        </div>
        <div v-if="recipe.allergens.length" class="rounded-xl2 border border-rose-200 bg-rose-50 p-3">
          <p class="mb-2 text-sm font-semibold text-rose-700">Contiene estos alérgenos:</p>
          <div class="flex flex-wrap gap-2"><AllergenBadge v-for="a in recipe.allergens" :key="a.id" :name="a.name" /></div>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <FavoriteButton v-model="favorite" :slug="recipe.slug" />
          <a :href="whatsappUrl" target="_blank" rel="noopener" class="btn-outline">
            <AppIcon name="whatsapp" :size="16" /> Compartir por WhatsApp
          </a>
        </div>
        <p v-if="recipe.summary" class="text-muted">{{ recipe.summary }}</p>
      </header>

      <section v-if="recipe.ingredients.length" class="card space-y-3 p-5">
        <h2 class="font-display text-xl text-ink">Ingredientes</h2>
        <ul class="list-disc space-y-1 pl-5 text-ink">
          <li v-for="(item, i) in recipe.ingredients" :key="i">
            <span v-if="item.quantity" class="font-semibold">{{ item.quantity }} </span>{{ item.name }}
          </li>
        </ul>
      </section>

      <section v-if="recipe.steps.length" class="card space-y-3 p-5">
        <h2 class="font-display text-xl text-ink">Preparación</h2>
        <ol class="list-decimal space-y-2 pl-5 text-ink">
          <li v-for="(step, i) in recipe.steps" :key="i" class="whitespace-pre-line">{{ step.text }}</li>
        </ol>
      </section>

      <section v-if="recipe.storage_tip" class="card space-y-2 p-5">
        <h2 class="font-display text-xl text-ink">Cómo conservarla</h2>
        <p class="whitespace-pre-line text-ink">{{ recipe.storage_tip }}</p>
      </section>

      <p class="text-xs text-muted">Actualizada: {{ new Date(recipe.updated_at).toLocaleDateString("es-CO") }}</p>
    </article>
  </div>
</template>
