<script setup lang="ts">
defineProps<{ title: string; saving?: boolean; error?: string }>();
const emit = defineEmits<{ (e: "save"): void; (e: "cancel"): void }>();
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 px-4 py-8">
      <form class="card w-full max-w-2xl space-y-4 p-6" @submit.prevent="emit('save')">
        <h2 class="font-display text-xl text-ink">{{ title }}</h2>
        <slot />
        <p v-if="error" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ error }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost" @click="emit('cancel')">Cancelar</button>
          <button type="submit" class="btn-primary" :disabled="saving">{{ saving ? "Guardando…" : "Guardar" }}</button>
        </div>
      </form>
    </div>
  </Teleport>
</template>
