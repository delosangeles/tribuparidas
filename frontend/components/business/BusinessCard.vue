<script setup lang="ts">
import type { Business } from "~/types";

defineProps<{ business: Business }>();
</script>

<template>
  <NuxtLink
    :to="`/emprendimientos/${business.slug}`"
    class="card group flex flex-col overflow-hidden transition hover:shadow-card"
  >
    <div class="relative aspect-[4/3] w-full overflow-hidden bg-gold-light p-6">
      <img
        v-if="business.logo"
        :src="business.logo"
        :alt="business.name"
        class="h-full w-full object-contain transition duration-300 group-hover:scale-105"
      />
      <div v-else class="flex h-full w-full items-center justify-center text-gold">
        <AppIcon name="briefcase" :size="40" />
      </div>
      <span v-if="business.tribe_benefit" class="badge absolute left-2 top-2 bg-white/90 text-gold-dark shadow-soft">
        Beneficio Tribu
      </span>
    </div>
    <div class="flex flex-1 flex-col items-center gap-1 p-4 text-center">
      <p class="font-semibold text-ink">{{ business.name }}</p>
      <p class="text-sm text-muted">{{ business.category?.name }}</p>
      <div class="mt-2 flex items-center justify-center gap-3">
        <span class="inline-flex items-center gap-1 text-xs text-muted">
          <AppIcon name="location" :size="14" />
          {{ business.city }}
        </span>
        <StarRating :rating="business.average_rating" :size="14" />
      </div>
    </div>
  </NuxtLink>
</template>
