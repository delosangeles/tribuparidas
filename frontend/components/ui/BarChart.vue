<script setup lang="ts">
const props = withDefaults(
  defineProps<{ items: { label: string; value: number }[]; orientation?: "vertical" | "horizontal" }>(),
  { orientation: "vertical" }
);

const MAX_BAR_PX = 160;
const max = computed(() => Math.max(1, ...props.items.map((i) => i.value)));

function barHeight(value: number) {
  return `${Math.max(4, Math.round((value / max.value) * MAX_BAR_PX))}px`;
}
function barWidthPct(value: number) {
  return `${Math.max(2, Math.round((value / max.value) * 100))}%`;
}
</script>

<template>
  <p v-if="!items.length" class="py-10 text-center text-sm text-muted">Todavía no hay datos suficientes.</p>

  <div v-else-if="orientation === 'vertical'" class="flex items-end gap-2 overflow-x-auto pb-1" :style="{ height: `${MAX_BAR_PX + 44}px` }">
    <div v-for="item in items" :key="item.label" class="flex min-w-[28px] flex-1 flex-col items-center justify-end gap-1">
      <span class="text-xs font-medium text-ink">{{ item.value }}</span>
      <div class="w-full rounded-t-md bg-gold" :style="{ height: barHeight(item.value) }" :title="`${item.label}: ${item.value}`" />
      <span class="whitespace-nowrap text-[10px] text-muted">{{ item.label }}</span>
    </div>
  </div>

  <div v-else class="space-y-2">
    <div v-for="item in items" :key="item.label" class="flex items-center gap-3">
      <span class="w-32 shrink-0 truncate text-xs text-muted sm:w-48" :title="item.label">{{ item.label }}</span>
      <div class="h-3 flex-1 overflow-hidden rounded-full bg-line">
        <div class="h-full rounded-full bg-gold" :style="{ width: barWidthPct(item.value) }" />
      </div>
      <span class="w-8 shrink-0 text-right text-xs font-medium text-ink">{{ item.value }}</span>
    </div>
  </div>
</template>
