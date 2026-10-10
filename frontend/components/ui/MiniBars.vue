<script setup lang="ts">
// Gráfica pequeña (sparkline de barras) para acompañar un texto. Resalta la barra más alta.
const props = defineProps<{ values: number[]; labels?: string[]; title: string; height?: number }>();

const max = computed(() => Math.max(1, ...props.values));
const peak = computed(() => props.values.indexOf(Math.max(...props.values)));
const h = computed(() => props.height ?? 56);
</script>

<template>
  <figure class="min-w-0">
    <figcaption class="mb-1 text-xs font-medium text-muted">{{ title }}</figcaption>
    <div class="flex items-end gap-px" :style="{ height: `${h}px` }" role="img" :aria-label="title">
      <div
        v-for="(value, i) in values"
        :key="i"
        class="flex-1 rounded-t-sm"
        :class="i === peak && value > 0 ? 'bg-gold' : 'bg-gold/40'"
        :style="{ height: `${Math.max(2, Math.round((value / max) * h))}px` }"
        :title="`${labels?.[i] ?? i + 1}: ${value}`"
      />
    </div>
    <div v-if="labels" class="mt-1 flex justify-between text-[10px] text-muted">
      <span>{{ labels[0] }}</span>
      <span>{{ labels[labels.length - 1] }}</span>
    </div>
  </figure>
</template>
