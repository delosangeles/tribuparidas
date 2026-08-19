<script setup lang="ts">
withDefaults(defineProps<{ label?: string }>(), { label: "Cargando..." });
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16 text-muted">
    <span class="h-8 w-8 animate-spin rounded-full border-2 border-gold-light border-t-gold" />
    <p class="text-sm">{{ label }}</p>
  </div>
</template>
