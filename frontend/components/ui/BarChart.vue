<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    items: { label: string; value: number; href?: string }[];
    orientation?: "vertical" | "horizontal";
  }>(),
  { orientation: "vertical" }
);

// Un string literal ("NuxtLink") pasado a <component :is> no se resuelve en
// runtime porque Nuxt no lo registra en el registro global de componentes;
// hay que resolverlo explícitamente para poder alternar entre link y div.
const NuxtLinkComponent = resolveComponent("NuxtLink");

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

  <div v-else class="space-y-1">
    <component
      :is="item.href ? NuxtLinkComponent : 'div'"
      v-for="item in items"
      :key="item.label"
      :to="item.href"
      class="-mx-2 flex flex-col gap-1 rounded-lg px-2 py-1.5 transition sm:flex-row sm:items-center sm:gap-3"
      :class="item.href ? 'hover:bg-gold-light/40 active:bg-gold-light/60' : ''"
    >
      <span
        class="break-all text-xs sm:w-48 sm:shrink-0 sm:truncate"
        :class="item.href ? 'font-medium text-gold' : 'text-muted'"
        :title="item.label"
      >
        {{ item.label }}
      </span>
      <div class="flex items-center gap-3">
        <div class="h-3 flex-1 overflow-hidden rounded-full bg-line">
          <div class="h-full rounded-full bg-gold" :style="{ width: barWidthPct(item.value) }" />
        </div>
        <span class="shrink-0 text-right text-xs font-medium text-ink">{{ item.value }}</span>
      </div>
    </component>
  </div>
</template>
