<script setup lang="ts">
withDefaults(defineProps<{ size?: "sm" | "md" }>(), { size: "md" });
</script>

<template>
  <span class="flex items-center gap-2 font-display font-bold text-ink" :class="size === 'sm' ? 'text-base' : 'text-lg'">
    <span
      class="flex items-center justify-center rounded-full bg-gold text-white"
      :class="size === 'sm' ? 'h-7 w-7' : 'h-8 w-8'"
    >
      <AppIcon name="logo" :size="size === 'sm' ? 14 : 16" />
    </span>
    Tribu Paridas
  </span>
</template>
