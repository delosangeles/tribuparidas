<script setup lang="ts">
import { categoryService } from "~/services/category.service";
import type { Category } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const categoriesStore = useCategoriesStore();
await categoriesStore.fetchAll(true);

const showForm = ref(false);
const editing = ref<Category | null>(null);
const form = reactive({ name: "", description: "", is_active: true, parent: null as number | null });
const imageFile = ref<File | null>(null);
const saving = ref(false);
const error = ref("");
const confirmDeleteSlug = ref<string | null>(null);
const deleteError = ref("");

function openCreate(parentId: number | null = null) {
  editing.value = null;
  form.name = "";
  form.description = "";
  form.is_active = true;
  form.parent = parentId;
  imageFile.value = null;
  showForm.value = true;
}

function openEdit(category: Category) {
  editing.value = category;
  form.name = category.name;
  form.description = category.description;
  form.is_active = category.is_active;
  form.parent = category.parent;
  imageFile.value = null;
  showForm.value = true;
}

async function handleSubmit() {
  saving.value = true;
  error.value = "";
  try {
    const payload = { ...form, parent: form.parent ?? "", image: imageFile.value };
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
    deleteError.value = "No se puede eliminar: hay emprendimientos o subcategorías usando esta categoría. Desactívala en su lugar.";
    confirmDeleteSlug.value = null;
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink">Categorías</h1>
        <p class="mt-1 text-sm text-muted">Organiza categorías principales y sus subcategorías.</p>
      </div>
      <button class="btn-primary" @click="openCreate()"><AppIcon name="plus" :size="16" /> Nueva categoría</button>
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
          <label class="mb-1 block text-sm font-medium text-ink">Categoría padre</label>
          <select v-model="form.parent" class="field">
            <option :value="null">Ninguna (es una categoría principal)</option>
            <option v-for="c in categoriesStore.items" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <p class="mt-1 text-xs text-muted">Solo se permiten dos niveles: categoría y subcategoría.</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Descripción</label>
          <textarea v-model="form.description" rows="2" class="field" />
        </div>
        <label class="flex items-center gap-2 text-sm text-ink">
          <input v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-line text-gold focus:ring-gold" />
          Categoría activa
        </label>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <div class="flex gap-2">
          <button type="submit" class="btn-primary" :disabled="saving">Guardar</button>
          <button type="button" class="btn-ghost" @click="showForm = false">Cancelar</button>
        </div>
      </form>
    </div>

    <div class="mt-6 space-y-4">
      <div v-for="category in categoriesStore.items" :key="category.id" class="card p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3">
            <span class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gold-light text-gold">
              <img v-if="category.image" :src="category.image" class="h-full w-full object-cover" />
              <AppIcon v-else name="box" :size="20" />
            </span>
            <div>
              <p class="font-medium text-ink">{{ category.name }}</p>
              <p class="text-xs text-muted">{{ category.businesses_count ?? 0 }} emprendimientos directos</p>
            </div>
          </div>
          <div class="flex shrink-0 gap-2">
            <button class="btn-outline !py-1 text-xs" @click="openCreate(category.id)">
              <AppIcon name="plus" :size="12" /> Subcategoría
            </button>
            <button class="btn-outline !py-1 text-xs" @click="openEdit(category)">Editar</button>
            <button class="btn-outline !py-1 text-xs !text-rose-500" @click="confirmDeleteSlug = category.slug">Borrar</button>
          </div>
        </div>

        <div v-if="category.subcategories?.length" class="ml-14 mt-3 space-y-2 border-l border-line pl-4">
          <div v-for="sub in category.subcategories" :key="sub.id" class="flex items-center justify-between gap-3 text-sm">
            <div>
              <p class="font-medium text-ink">{{ sub.name }}</p>
              <p class="text-xs text-muted">{{ sub.businesses_count ?? 0 }} emprendimientos</p>
            </div>
            <div class="flex shrink-0 gap-2">
              <button class="btn-outline !py-1 text-xs" @click="openEdit(sub)">Editar</button>
              <button class="btn-outline !py-1 text-xs !text-rose-500" @click="confirmDeleteSlug = sub.slug">Borrar</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <p v-if="deleteError" class="mt-4 text-sm text-rose-500">{{ deleteError }}</p>

    <ConfirmDialog
      :open="confirmDeleteSlug !== null"
      title="¿Eliminar categoría?"
      description="Solo se puede eliminar si ningún emprendimiento o subcategoría la está usando."
      confirm-label="Eliminar"
      danger
      @confirm="confirmDelete"
      @cancel="confirmDeleteSlug = null"
    />
  </div>
</template>
