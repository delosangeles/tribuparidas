<script setup lang="ts">
withDefaults(
  defineProps<{ open: boolean; title: string; description?: string; confirmLabel?: string; danger?: boolean }>(),
  { confirmLabel: "Confirmar", danger: false }
);
const emit = defineEmits<{ (e: "confirm"): void; (e: "cancel"): void }>();
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
      <div class="card w-full max-w-sm p-6">
        <p class="text-lg font-semibold text-ink">{{ title }}</p>
        <p v-if="description" class="mt-2 text-sm text-muted">{{ description }}</p>
        <div class="mt-6 flex justify-end gap-2">
          <button class="btn-ghost" @click="emit('cancel')">Cancelar</button>
          <button
            class="btn-primary"
            :class="danger && '!bg-rose-500 hover:!bg-rose-600'"
            @click="emit('confirm')"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
