<script setup lang="ts">
import type { Category } from "~/types";

defineProps<{ category: Category }>();
</script>

<template>
  <NuxtLink
    :to="`/businesses?category=${category.slug}`"
    class="flex flex-col items-center gap-2 text-center"
  >
    <span class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-pink-light text-pink transition hover:bg-pink hover:text-white">
      <img v-if="category.image" :src="category.image" :alt="category.name" class="h-full w-full object-cover" />
      <AppIcon v-else name="box" :size="24" />
    </span>
    <span class="text-xs font-medium text-ink">{{ category.name }}</span>
  </NuxtLink>
</template>
