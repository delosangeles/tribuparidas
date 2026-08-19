<script setup lang="ts">
import type { Product } from "~/types";

const props = defineProps<{ initial?: Product | null; loading?: boolean }>();
const emit = defineEmits<{ (e: "submit", payload: any): void; (e: "cancel"): void }>();

const form = reactive({
  name: props.initial?.name || "",
  price: props.initial?.price || "",
  description: props.initial?.description || "",
  is_active: props.initial?.is_active ?? true,
});
const imageFile = ref<File | null>(null);

function handleSubmit() {
  emit("submit", { ...form, image: imageFile.value });
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="handleSubmit">
    <ImageUploader :model-value="initial?.image" label="Foto del producto" @select="(f) => (imageFile = f)" />
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
      <input v-model="form.name" type="text" required class="field" />
    </div>
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Precio (COP)</label>
      <input v-model="form.price" type="number" min="0" step="1" required class="field" />
    </div>
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">Descripción</label>
      <textarea v-model="form.description" rows="3" class="field" />
    </div>
    <label class="flex items-center gap-2 text-sm text-ink">
      <input v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-line text-gold focus:ring-gold" />
      Producto visible en mi perfil
    </label>
    <div class="flex gap-2">
      <button type="submit" class="btn-primary" :disabled="loading">{{ loading ? "Guardando..." : "Guardar producto" }}</button>
      <button type="button" class="btn-ghost" @click="emit('cancel')">Cancelar</button>
    </div>
  </form>
</template>
