<script setup lang="ts">
withDefaults(defineProps<{ size?: "sm" | "md" }>(), { size: "md" });
</script>

<template>
  <span class="flex items-center gap-2 font-display font-bold text-ink" :class="size === 'sm' ? 'text-base' : 'text-lg'">
    <img
      :src="useAssetUrl('logo-mark.png')"
      alt="Tribu Paridas"
      class="shrink-0"
      :class="size === 'sm' ? 'h-7 w-7' : 'h-8 w-8'"
    />
    Tribu Paridas
  </span>
</template>
