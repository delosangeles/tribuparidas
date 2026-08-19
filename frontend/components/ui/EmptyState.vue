<script setup lang="ts">
withDefaults(
  defineProps<{ icon?: string; title: string; description?: string }>(),
  { icon: "box" }
);
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 rounded-xl2 border border-dashed border-line bg-white/60 px-6 py-14 text-center">
    <span class="flex h-12 w-12 items-center justify-center rounded-full bg-gold-light text-gold">
      <AppIcon :name="icon" :size="24" />
    </span>
    <p class="font-semibold text-ink">{{ title }}</p>
    <p v-if="description" class="max-w-sm text-sm text-muted">{{ description }}</p>
    <slot />
  </div>
</template>
