<script setup lang="ts">
const props = defineProps<{ page: number; hasNext: boolean; hasPrevious: boolean }>();
const emit = defineEmits<{ (e: "update:page", value: number): void }>();
</script>

<template>
  <div class="flex items-center justify-center gap-3 pt-4">
    <button class="btn-outline" :disabled="!hasPrevious" @click="emit('update:page', props.page - 1)">
      <AppIcon name="arrow" :size="16" class="rotate-180" />
      Anterior
    </button>
    <span class="text-sm text-muted">Página {{ page }}</span>
    <button class="btn-outline" :disabled="!hasNext" @click="emit('update:page', props.page + 1)">
      Siguiente
      <AppIcon name="arrow" :size="16" />
    </button>
  </div>
</template>
