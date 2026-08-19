<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { Business } from "~/types";

const categoriesStore = useCategoriesStore();
await categoriesStore.fetchAll();

const { data: featured } = await useAsyncData("featured-businesses", async () => {
  const { data } = await businessService.list({ ordering: "-average_rating", page_size: 8 });
  return data.results;
});

const searchQuery = ref("");
function submitSearch() {
  navigateTo({ path: "/businesses", query: searchQuery.value ? { search: searchQuery.value } : {} });
}
</script>

<template>
  <div>
    <section class="relative overflow-hidden">
      <div class="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-20">
        <div>
          <h1 class="text-4xl font-bold leading-tight text-ink sm:text-5xl">
            Descubre emprendimientos
            <br />
            <span class="text-gold">hechos con pasión ♡</span>
          </h1>
          <p class="mt-4 max-w-md text-muted">
            Conoce productos y servicios de personas que están construyendo sus propios sueños.
          </p>

          <form class="mt-6 flex max-w-lg gap-2 rounded-full border border-line bg-white p-1.5 shadow-soft" @submit.prevent="submitSearch">
            <span class="flex items-center pl-3 text-muted">
              <AppIcon name="search" :size="18" />
            </span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Buscar emprendimiento, producto o categoría..."
              class="flex-1 border-none bg-transparent px-2 text-sm outline-none"
            />
            <button type="submit" class="btn-primary">Buscar</button>
          </form>

          <div class="mt-8 grid grid-cols-4 gap-4 sm:grid-cols-8">
            <CategoryPill v-for="category in categoriesStore.items.slice(0, 7)" :key="category.id" :category="category" />
            <NuxtLink to="/businesses" class="flex flex-col items-center gap-2 text-center">
              <span class="flex h-16 w-16 items-center justify-center rounded-full bg-ink/5 text-ink transition hover:bg-gold hover:text-white">
                <AppIcon name="menu" :size="22" />
              </span>
              <span class="text-xs font-medium text-ink">Ver todas</span>
            </NuxtLink>
          </div>
        </div>

        <div class="relative mx-auto flex h-72 w-72 items-center justify-center sm:h-96 sm:w-96">
          <span class="absolute inset-0 rounded-full bg-gold-light" />
          <span class="absolute inset-6 rounded-full border-2 border-dashed border-gold/40" />
          <span class="relative flex h-40 w-40 items-center justify-center rounded-full bg-white text-gold shadow-card sm:h-52 sm:w-52">
            <AppIcon name="logo" :size="72" />
          </span>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-xl font-bold text-ink">
          <AppIcon name="heart" :size="18" class="text-gold" />
          Emprendimientos destacados
        </h2>
        <NuxtLink to="/businesses" class="text-sm font-semibold text-gold hover:underline">Ver todos</NuxtLink>
      </div>

      <div v-if="featured?.length" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <BusinessCard v-for="business in featured" :key="business.id" :business="business as Business" />
      </div>
      <EmptyState v-else icon="briefcase" title="Todavía no hay emprendimientos publicados" description="Vuelve pronto, estamos sumando nuevas historias." />
    </section>
  </div>
</template>
