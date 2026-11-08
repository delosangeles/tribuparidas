<script setup lang="ts">
import type { RecipeSummary } from "~/types/alimentacion";
import { prepTimeLabel } from "~/utils/alimentacion";

const props = defineProps<{ recipe: RecipeSummary; preview?: boolean }>();
const emit = defineEmits<{ (e: "favorite", value: boolean): void }>();

const favorite = computed({
  get: () => props.recipe.is_favorite,
  set: (value: boolean) => emit("favorite", value),
});
</script>

<template>
  <NuxtLink
    :to="{ path: `/alimentacion-complementaria/${recipe.slug}`, query: preview ? { preview: 1 } : {} }"
    class="card group flex flex-col overflow-hidden transition hover:shadow-card"
  >
    <div class="relative aspect-[4/3] bg-gold-light/40">
      <img v-if="recipe.image" :src="recipe.image" :alt="recipe.title" loading="lazy" class="h-full w-full object-cover" />
      <div v-else class="flex h-full items-center justify-center text-gold"><AppIcon name="leaf" :size="40" /></div>
      <div class="absolute right-2 top-2">
        <FavoriteButton v-model="favorite" :slug="recipe.slug" />
      </div>
      <span v-if="recipe.status === 'draft'" class="badge absolute left-2 top-2 bg-ink/80 text-white">Borrador</span>
    </div>
    <div class="flex flex-1 flex-col gap-3 p-4">
      <h3 class="font-display text-lg leading-snug text-ink group-hover:text-gold-dark">{{ recipe.title }}</h3>
      <div class="flex flex-wrap items-center gap-2 text-xs text-muted">
        <span class="badge bg-gold-light text-gold-dark">{{ recipe.age_range.name }}</span>
        <span>{{ recipe.meal_type.name }}</span>
        <span v-if="recipe.prep_time_minutes" class="flex items-center gap-1">
          <AppIcon name="clock" :size="12" /> {{ prepTimeLabel(recipe.prep_time_minutes) }}
        </span>
      </div>
      <div class="mt-auto flex flex-wrap gap-1.5">
        <AllergenBadge v-for="allergen in recipe.allergens" :key="allergen.id" :name="allergen.name" />
      </div>
    </div>
  </NuxtLink>
</template>
