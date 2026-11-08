<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { Catalogs, FoodItem, GuideSummary, RecipeSummary, SafetyContent } from "~/types/alimentacion";
import { filterRecipes } from "~/utils/alimentacion";

definePageMeta({ middleware: "alimentacion" });

const route = useRoute();
const authStore = useAuthStore();
const preview = computed(() => route.query.preview === "1" && authStore.hasModule("alimentacion"));

usePageSeo({
  title: "Alimentación complementaria",
  description: "Guía y recetas para acompañar el inicio de la alimentación de tu bebé desde los 6 meses.",
  path: "/alimentacion-complementaria",
});

type Tab = "recetas" | "guia" | "alimentos" | "seguridad";
const TABS: { key: Tab; label: string }[] = [
  { key: "recetas", label: "Recetas" },
  { key: "guia", label: "Guía de inicio" },
  { key: "alimentos", label: "Alimentos" },
  { key: "seguridad", label: "Seguridad" },
];
const tab = ref<Tab>((TABS.find((t) => t.key === route.query.seccion)?.key ?? "recetas") as Tab);
watch(tab, (value) => navigateTo({ query: { ...route.query, seccion: value } }, { replace: true }));

const recipes = ref<RecipeSummary[]>([]);
const guides = ref<GuideSummary[]>([]);
const foods = ref<FoodItem[]>([]);
const safety = ref<SafetyContent | null>(null);
const catalogs = ref<Catalogs>({ ages: [], meal_types: [], allergens: [] });
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  const params = preview.value ? { preview: "1" } : undefined;
  try {
    const [c, r, g, f, s] = await Promise.all([
      alimentacionService.catalogs(),
      alimentacionService.recipes(params),
      alimentacionService.guides(preview.value),
      alimentacionService.foods(preview.value),
      alimentacionService.safety(preview.value),
    ]);
    catalogs.value = c.data;
    recipes.value = r.data;
    guides.value = g.data;
    foods.value = f.data;
    safety.value = s.data;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
onMounted(load);

// ---- buscador y filtros (en el cliente, en tiempo real y sin distinguir tildes)
const q = ref("");
const age = ref("");
const mealType = ref("");
const withoutAllergens = ref<string[]>([]);

const filtered = computed(() =>
  filterRecipes(recipes.value, { q: q.value, age: age.value, mealType: mealType.value, withoutAllergens: withoutAllergens.value })
);
const hasFilters = computed(() => Boolean(q.value || age.value || mealType.value || withoutAllergens.value.length));

function toggleAllergen(slug: string) {
  const list = withoutAllergens.value;
  withoutAllergens.value = list.includes(slug) ? list.filter((s) => s !== slug) : [...list, slug];
}
function clearFilters() {
  q.value = "";
  age.value = "";
  mealType.value = "";
  withoutAllergens.value = [];
}
function setFavorite(recipe: RecipeSummary, value: boolean) {
  recipe.is_favorite = value;
}

const filteredFoods = computed(() => (age.value ? foods.value.filter((f) => f.age_range?.slug === age.value) : foods.value));
const queryParam = computed(() => (preview.value ? { preview: 1 } : {}));
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
    <header class="space-y-2">
      <h1 class="font-display text-3xl text-ink sm:text-4xl">Alimentación complementaria</h1>
      <p class="max-w-2xl text-muted">Guía y recetas para acompañar el inicio de la alimentación de tu bebé desde los 6 meses.</p>
    </header>

    <MedicalDisclaimer />

    <p v-if="preview" class="rounded-xl2 bg-ink px-4 py-2 text-sm text-white">
      Vista previa del equipo: se incluyen los borradores. Las usuarias no los ven.
    </p>

    <nav class="flex gap-1 overflow-x-auto border-b border-line" aria-label="Secciones">
      <button
        v-for="item in TABS"
        :key="item.key"
        type="button"
        class="whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-semibold transition"
        :class="tab === item.key ? 'border-gold text-gold-dark' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
      <NuxtLink
        v-if="authStore.isAuthenticated"
        to="/alimentacion-complementaria/favoritos"
        class="ml-auto flex items-center gap-1 whitespace-nowrap px-4 py-2.5 text-sm font-semibold text-muted hover:text-gold"
      >
        <AppIcon name="heart" :size="14" /> Mis favoritos
      </NuxtLink>
    </nav>

    <LoadingSpinner v-if="loading" />
    <p v-else-if="error" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">{{ error }}</p>

    <template v-else>
      <!-- Recetas -->
      <section v-if="tab === 'recetas'" class="space-y-5">
        <div class="space-y-3">
          <div class="relative">
            <AppIcon name="search" :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
            <input v-model="q" type="search" class="input !pl-10" placeholder="Busca por receta o ingrediente…" aria-label="Buscar recetas" />
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <select v-model="age" class="input" aria-label="Edad">
              <option value="">Todas las edades</option>
              <option v-for="a in catalogs.ages" :key="a.id" :value="a.slug">{{ a.name }}</option>
            </select>
            <select v-model="mealType" class="input" aria-label="Tipo de comida">
              <option value="">Todos los tipos</option>
              <option v-for="m in catalogs.meal_types" :key="m.id" :value="m.slug">{{ m.name }}</option>
            </select>
          </div>
          <div v-if="catalogs.allergens.length" class="space-y-1.5">
            <p class="text-xs font-semibold uppercase tracking-wide text-muted">Sin estos alérgenos</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="allergen in catalogs.allergens"
                :key="allergen.id"
                type="button"
                class="rounded-full border px-3 py-1 text-xs font-semibold transition"
                :class="withoutAllergens.includes(allergen.slug) ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-line bg-white text-muted hover:border-gold'"
                :aria-pressed="withoutAllergens.includes(allergen.slug)"
                @click="toggleAllergen(allergen.slug)"
              >
                {{ allergen.name }}
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between text-sm text-muted">
          <span>{{ filtered.length }} {{ filtered.length === 1 ? "receta" : "recetas" }}</span>
          <button v-if="hasFilters" type="button" class="btn-ghost !py-1" @click="clearFilters">Limpiar filtros</button>
        </div>

        <div v-if="filtered.length" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <RecipeCard v-for="recipe in filtered" :key="recipe.id" :recipe="recipe" :preview="preview" @favorite="setFavorite(recipe, $event)" />
        </div>
        <EmptyState v-else icon="leaf" :title="hasFilters ? 'No encontramos recetas con esos filtros' : 'Pronto tendremos recetas para ti'" />
      </section>

      <!-- Guía de inicio -->
      <section v-else-if="tab === 'guia'" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <NuxtLink
          v-for="guide in guides"
          :key="guide.id"
          :to="{ path: `/alimentacion-complementaria/guias/${guide.slug}`, query: queryParam }"
          class="card flex flex-col overflow-hidden transition hover:shadow-card"
        >
          <img v-if="guide.image" :src="guide.image" :alt="guide.title" loading="lazy" class="aspect-[16/9] w-full object-cover" />
          <div class="space-y-2 p-4">
            <h3 class="font-display text-lg text-ink">{{ guide.title }}</h3>
            <p class="line-clamp-3 text-sm text-muted">{{ guide.summary }}</p>
            <p class="text-xs text-muted">Actualizada: {{ new Date(guide.updated_at).toLocaleDateString("es-CO") }}</p>
          </div>
        </NuxtLink>
        <div v-if="!guides.length" class="sm:col-span-2 lg:col-span-3">
          <EmptyState icon="file-text" title="Pronto tendremos guías para ti" />
        </div>
      </section>

      <!-- Introducción de alimentos -->
      <section v-else-if="tab === 'alimentos'" class="space-y-4">
        <select v-model="age" class="input sm:max-w-xs" aria-label="Edad">
          <option value="">Todas las edades</option>
          <option v-for="a in catalogs.ages" :key="a.id" :value="a.slug">{{ a.name }}</option>
        </select>
        <ul v-if="filteredFoods.length" class="grid gap-4 sm:grid-cols-2">
          <li v-for="food in filteredFoods" :key="food.id" class="card space-y-2 p-4">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="font-display text-lg text-ink">{{ food.name }}</h3>
              <span v-if="food.age_range" class="badge bg-gold-light text-gold-dark">{{ food.age_range.name }}</span>
              <AllergenBadge v-if="food.is_common_allergen" :name="food.allergen?.name ? `Alérgeno frecuente: ${food.allergen.name}` : 'Alérgeno frecuente'" />
            </div>
            <p class="whitespace-pre-line text-sm text-muted">{{ food.how_to_offer }}</p>
          </li>
        </ul>
        <EmptyState v-else icon="leaf" title="Pronto tendremos esta información" />
      </section>

      <!-- Seguridad -->
      <section v-else class="space-y-4">
        <article v-if="safety && safety.published" class="card space-y-4 p-6">
          <h2 class="font-display text-2xl text-ink">Seguridad al comer</h2>
          <div class="rich-content text-ink" v-html="safety.content" />
          <footer class="border-t border-line pt-3 text-sm text-muted">
            Redactado por <strong class="text-ink">{{ safety.professional_name }}</strong>
            <span v-if="safety.professional_title">, {{ safety.professional_title }}</span>.
            <span v-if="safety.reviewed_on"> Revisado el {{ new Date(`${safety.reviewed_on}T00:00:00`).toLocaleDateString("es-CO") }}.</span>
          </footer>
        </article>
        <EmptyState v-else icon="shield" title="Esta sección estará disponible pronto" description="La redacta y firma un profesional antes de publicarse." />
      </section>
    </template>
  </div>
</template>
