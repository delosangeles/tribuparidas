<script setup lang="ts">
import type { Business } from "~/types";

defineProps<{ business: Business }>();
</script>

<template>
  <NuxtLink
    :to="`/businesses/${business.slug}`"
    class="card group flex flex-col overflow-hidden transition hover:shadow-card"
  >
    <div class="aspect-[4/3] w-full overflow-hidden bg-pink-light">
      <img
        v-if="business.cover_image"
        :src="business.cover_image"
        :alt="business.name"
        class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
      />
      <div v-else class="flex h-full w-full items-center justify-center text-pink">
        <AppIcon name="images" :size="32" />
      </div>
    </div>
    <div class="flex flex-1 flex-col gap-1 p-4">
      <p class="font-semibold text-ink">{{ business.name }}</p>
      <p class="text-sm text-muted">{{ business.category?.name }}</p>
      <div class="mt-2 flex items-center justify-between">
        <span class="inline-flex items-center gap-1 text-xs text-muted">
          <AppIcon name="location" :size="14" />
          {{ business.city }}
        </span>
        <StarRating :rating="business.average_rating" :size="14" />
      </div>
    </div>
  </NuxtLink>
</template>
