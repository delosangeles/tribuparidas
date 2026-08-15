<script setup lang="ts">
withDefaults(
  defineProps<{ label: string; value: string | number; icon?: string; trend?: string; trendPositive?: boolean }>(),
  { icon: "box", trendPositive: true }
);
</script>

<template>
  <div class="card p-5">
    <div class="flex items-start justify-between">
      <p class="text-sm text-muted">{{ label }}</p>
      <span class="flex h-9 w-9 items-center justify-center rounded-full bg-pink-light text-pink">
        <AppIcon :name="icon" :size="18" />
      </span>
    </div>
    <p class="mt-3 text-2xl font-bold text-ink">{{ value }}</p>
    <p v-if="trend" class="mt-1 text-xs font-medium" :class="trendPositive ? 'text-emerald-600' : 'text-muted'">
      {{ trend }}
    </p>
  </div>
</template>
