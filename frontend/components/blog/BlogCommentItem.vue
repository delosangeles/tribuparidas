<script setup lang="ts">
import type { BlogComment } from "~/types";

defineProps<{ comment: BlogComment }>();

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}
</script>

<template>
  <div class="border-b border-line py-4 last:border-0">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="flex h-9 w-9 items-center justify-center rounded-full bg-gold-light text-sm font-semibold text-gold">
          {{ comment.author_name?.charAt(0) || "?" }}
        </span>
        <p class="text-sm font-semibold text-ink">{{ comment.author_name }}</p>
      </div>
      <span class="text-xs text-muted">{{ formatDate(comment.created_at) }}</span>
    </div>
    <p class="ml-12 mt-2 whitespace-pre-line text-sm text-ink">{{ comment.content }}</p>
  </div>
</template>
