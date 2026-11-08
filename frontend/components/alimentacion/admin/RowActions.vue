<script setup lang="ts">
// Botones de una fila: ordenar, vista previa, publicar/ocultar, editar y eliminar.
// Cada uno se muestra según el permiso de la usuaria (el servidor también lo exige).
defineProps<{
  index: number;
  total: number;
  status?: string;
  previewTo?: string;
  canEdit: boolean;
  canApprove: boolean;
  canDelete: boolean;
}>();
const emit = defineEmits<{
  (e: "move", delta: number): void;
  (e: "toggle"): void;
  (e: "edit"): void;
  (e: "remove"): void;
}>();
</script>

<template>
  <div class="flex flex-wrap items-center gap-1">
    <template v-if="canEdit">
      <button type="button" class="btn-ghost !px-2" :disabled="index === 0" aria-label="Subir" @click="emit('move', -1)">↑</button>
      <button type="button" class="btn-ghost !px-2" :disabled="index === total - 1" aria-label="Bajar" @click="emit('move', 1)">↓</button>
    </template>
    <NuxtLink v-if="previewTo" :to="previewTo" target="_blank" class="btn-ghost !px-3">Vista previa</NuxtLink>
    <button v-if="status && canApprove" type="button" class="btn-outline !px-3 !py-1.5" @click="emit('toggle')">
      {{ status === "published" ? "Ocultar" : "Publicar" }}
    </button>
    <button v-if="canEdit" type="button" class="btn-ghost !px-3" @click="emit('edit')">Editar</button>
    <button v-if="canDelete" type="button" class="btn-ghost !px-3 !text-rose-500" @click="emit('remove')">Eliminar</button>
  </div>
</template>
