<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<template>
  <span class="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
    <AppIcon name="shield" :size="12" /> {{ name }}
  </span>
</template>
