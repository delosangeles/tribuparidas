<script setup lang="ts">
const props = withDefaults(
  defineProps<{ rating: number | string; size?: number; showValue?: boolean }>(),
  { size: 16, showValue: true }
);

const value = computed(() => Number(props.rating) || 0);
</script>

<template>
  <span class="inline-flex items-center gap-1 text-amber-500">
    <AppIcon name="star" :size="size" class="fill-current" />
    <span v-if="showValue" class="text-sm font-medium text-ink">{{ value.toFixed(1) }}</span>
  </span>
</template>
