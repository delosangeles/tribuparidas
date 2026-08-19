<script setup lang="ts">
import type { Review } from "~/types";

defineProps<{ review: Review }>();

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}
</script>

<template>
  <div class="border-b border-line py-4 last:border-0">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="flex h-9 w-9 items-center justify-center rounded-full bg-gold-light text-sm font-semibold text-gold">
          {{ review.user_name?.charAt(0) || "?" }}
        </span>
        <div>
          <p class="text-sm font-semibold text-ink">{{ review.user_name }}</p>
          <StarRating :rating="review.rating" :size="12" />
        </div>
      </div>
      <span class="text-xs text-muted">{{ formatDate(review.created_at) }}</span>
    </div>
    <p v-if="review.comment" class="ml-12 mt-2 text-sm text-ink">{{ review.comment }}</p>
  </div>
</template>
