<script setup lang="ts">
import { categoryService } from "~/services/category.service";
import type { Category } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const categoriesStore = useCategoriesStore();
await categoriesStore.fetchAll(true);

const showForm = ref(false);
const editing = ref<Category | null>(null);
const form = reactive({ name: "", description: "", is_active: true });
const imageFile = ref<File | null>(null);
const saving = ref(false);
const error = ref("");
const confirmDeleteSlug = ref<string | null>(null);
const deleteError = ref("");

function openCreate() {
  editing.value = null;
  form.name = "";
  form.description = "";
  form.is_active = true;
  imageFile.value = null;
  showForm.value = true;
}

function openEdit(category: Category) {
  editing.value = category;
  form.name = category.name;
  form.description = category.description;
  form.is_active = category.is_active;
  imageFile.value = null;
  showForm.value = true;
}

async function handleSubmit() {
  saving.value = true;
  error.value = "";
  try {
    const payload = { ...form, image: imageFile.value };
    if (editing.value) {
      await categoryService.update(editing.value.slug, payload);
    } else {
      await categoryService.create(payload);
    }
    showForm.value = false;
    await categoriesStore.fetchAll(true);
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}

async function confirmDelete() {
  if (!confirmDeleteSlug.value) return;
  deleteError.value = "";
  try {
    await categoryService.remove(confirmDeleteSlug.value);
    confirmDeleteSlug.value = null;
    await categoriesStore.fetchAll(true);
  } catch (err) {
    deleteError.value = "No se puede eliminar: hay emprendimientos usando esta categoría. Desactívala en su lugar.";
    confirmDeleteSlug.value = null;
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink">Categorías</h1>
        <p class="mt-1 text-sm text-muted">Organiza los tipos de emprendimientos disponibles.</p>
      </div>
      <button class="btn-primary" @click="openCreate"><AppIcon name="plus" :size="16" /> Nueva categoría</button>
    </div>

    <div v-if="showForm" class="card mt-6 p-6">
      <p class="mb-4 font-semibold text-ink">{{ editing ? "Editar categoría" : "Nueva categoría" }}</p>
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <ImageUploader :model-value="editing?.image" label="Ícono" @select="(f) => (imageFile = f)" />
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
          <input v-model="form.name" type="text" required class="field" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Descripción</label>
          <textarea v-model="form.description" rows="2" class="field" />
        </div>
        <label class="flex items-center gap-2 text-sm text-ink">
          <input v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-line text-pink focus:ring-pink" />
          Categoría activa
        </label>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <div class="flex gap-2">
          <button type="submit" class="btn-primary" :disabled="saving">Guardar</button>
          <button type="button" class="btn-ghost" @click="showForm = false">Cancelar</button>
        </div>
      </form>
    </div>

    <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <div v-for="category in categoriesStore.items" :key="category.id" class="card p-4">
        <span class="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-pink-light text-pink">
          <img v-if="category.image" :src="category.image" class="h-full w-full object-cover" />
          <AppIcon v-else name="box" :size="20" />
        </span>
        <p class="mt-3 font-medium text-ink">{{ category.name }}</p>
        <p class="text-xs text-muted">{{ category.businesses_count ?? 0 }} emprendimientos</p>
        <div class="mt-3 flex gap-2">
          <button class="btn-outline flex-1 !py-1 text-xs" @click="openEdit(category)">Editar</button>
          <button class="btn-outline flex-1 !py-1 text-xs !text-rose-500" @click="confirmDeleteSlug = category.slug">Borrar</button>
        </div>
      </div>
    </div>

    <p v-if="deleteError" class="mt-4 text-sm text-rose-500">{{ deleteError }}</p>

    <ConfirmDialog
      :open="confirmDeleteSlug !== null"
      title="¿Eliminar categoría?"
      description="Solo se puede eliminar si ningún emprendimiento la está usando."
      confirm-label="Eliminar"
      danger
      @confirm="confirmDelete"
      @cancel="confirmDeleteSlug = null"
    />
  </div>
</template>
