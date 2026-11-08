<script setup lang="ts">
import type { CatalogItem, RecipeAdmin } from "~/types/alimentacion";

const props = defineProps<{ ages: CatalogItem[]; mealTypes: CatalogItem[]; allergens: CatalogItem[] }>();

const authStore = useAuthStore();
const canAdd = computed(() => authStore.can("alimentacion", "add"));
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canApprove = computed(() => authStore.can("alimentacion", "approve"));
const canDelete = computed(() => authStore.can("alimentacion", "delete"));

const crud = useAdminCrud<RecipeAdmin>("recetas");
const statusFilter = ref("");
const search = ref("");
const reload = () => crud.load({ ...(statusFilter.value ? { status: statusFilter.value } : {}), ...(search.value ? { q: search.value } : {}) });
await reload();
watch([statusFilter, search], reload);

const nameOf = (list: CatalogItem[], id: number) => list.find((i) => i.id === id)?.name ?? "—";

// ---- formulario
type Form = Omit<RecipeAdmin, "id" | "slug" | "image" | "updated_at" | "order">;
const blank = (): Form => ({
  title: "", summary: "", age_range: props.ages[0]?.id ?? 0, meal_type: props.mealTypes[0]?.id ?? 0,
  prep_time_minutes: null, allergens: [], storage_tip: "", ingredients: [{ name: "", quantity: "" }], steps: [{ text: "" }], status: "draft",
});
const editing = ref<RecipeAdmin | "new" | null>(null);
const form = reactive<Form>(blank());
const image = ref<File | null>(null);
const saving = ref(false);
const formError = ref("");

function open(recipe?: RecipeAdmin) {
  Object.assign(form, recipe ? {
    title: recipe.title, summary: recipe.summary, age_range: recipe.age_range, meal_type: recipe.meal_type,
    prep_time_minutes: recipe.prep_time_minutes, allergens: [...recipe.allergens], storage_tip: recipe.storage_tip,
    ingredients: recipe.ingredients.length ? recipe.ingredients.map((i) => ({ ...i })) : [{ name: "", quantity: "" }],
    steps: recipe.steps.length ? recipe.steps.map((s) => ({ ...s })) : [{ text: "" }], status: recipe.status,
  } : blank());
  image.value = null;
  formError.value = "";
  editing.value = recipe ?? "new";
}

async function save() {
  saving.value = true;
  formError.value = "";
  try {
    const payload = {
      ...form,
      ingredients: form.ingredients.filter((i) => i.name.trim()),
      steps: form.steps.filter((s) => s.text.trim()),
    };
    await crud.save(payload, editing.value === "new" ? null : (editing.value as RecipeAdmin).id, image.value);
    editing.value = null;
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}

function toggleAllergen(id: number) {
  form.allergens = form.allergens.includes(id) ? form.allergens.filter((a) => a !== id) : [...form.allergens, id];
}

const removeTarget = ref<RecipeAdmin | null>(null);
const actionError = ref("");
async function guard(fn: () => Promise<unknown>) {
  actionError.value = "";
  try { await fn(); } catch (err) { actionError.value = useErrorMessage(err); }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <input v-model="search" type="search" class="input sm:max-w-xs" placeholder="Buscar receta…" aria-label="Buscar" />
      <select v-model="statusFilter" class="input sm:max-w-[10rem]" aria-label="Estado">
        <option value="">Todas</option>
        <option value="published">Publicadas</option>
        <option value="draft">Borradores</option>
      </select>
      <button v-if="canAdd" class="btn-primary ml-auto" :disabled="!ages.length || !mealTypes.length" @click="open()">Nueva receta</button>
    </div>
    <p v-if="actionError || crud.error.value" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ actionError || crud.error.value }}</p>

    <ul class="space-y-2">
      <li v-for="(item, index) in crud.items.value" :key="item.id" class="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div class="min-w-0">
          <p class="font-semibold text-ink">{{ item.title }}</p>
          <p class="text-xs text-muted">{{ nameOf(ages, item.age_range) }} · {{ nameOf(mealTypes, item.meal_type) }}</p>
          <span :class="item.status === 'published' ? 'badge-approved' : 'badge-pending'">{{ item.status === "published" ? "Publicada" : "Borrador" }}</span>
        </div>
        <RowActions
          :index="index" :total="crud.items.value.length" :status="item.status"
          :preview-to="`/alimentacion-complementaria/${item.slug}?preview=1`"
          :can-edit="canEdit" :can-approve="canApprove" :can-delete="canDelete"
          @move="guard(() => crud.move(index, $event))"
          @toggle="guard(() => crud.setPublished(item, item.status !== 'published'))"
          @edit="open(item)" @remove="removeTarget = item"
        />
      </li>
    </ul>
    <EmptyState v-if="!crud.items.value.length && !crud.loading.value" icon="leaf" title="Todavía no hay recetas" />

    <AdminModal v-if="editing" :title="editing === 'new' ? 'Nueva receta' : 'Editar receta'" :saving="saving" :error="formError" @save="save" @cancel="editing = null">
      <label class="block text-sm font-medium">Título<input v-model="form.title" class="input mt-1" required maxlength="200" /></label>
      <label class="block text-sm font-medium">Resumen<textarea v-model="form.summary" class="field mt-1" rows="2" /></label>
      <div class="grid gap-3 sm:grid-cols-3">
        <label class="block text-sm font-medium">Edad
          <select v-model.number="form.age_range" class="input mt-1" required>
            <option v-for="a in ages" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </label>
        <label class="block text-sm font-medium">Tipo
          <select v-model.number="form.meal_type" class="input mt-1" required>
            <option v-for="m in mealTypes" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </label>
        <label class="block text-sm font-medium">Preparación (min)
          <input v-model.number="form.prep_time_minutes" type="number" min="0" max="1440" class="input mt-1" />
        </label>
      </div>
      <fieldset class="space-y-1">
        <legend class="text-sm font-medium">Alérgenos presentes</legend>
        <div class="flex flex-wrap gap-3">
          <label v-for="al in allergens" :key="al.id" class="flex items-center gap-1.5 text-sm">
            <input type="checkbox" :checked="form.allergens.includes(al.id)" @change="toggleAllergen(al.id)" /> {{ al.name }}
          </label>
          <span v-if="!allergens.length" class="text-xs text-muted">Crea los alérgenos en la pestaña Catálogos.</span>
        </div>
      </fieldset>
      <fieldset class="space-y-2">
        <legend class="text-sm font-medium">Ingredientes</legend>
        <div v-for="(ing, i) in form.ingredients" :key="i" class="flex gap-2">
          <input v-model="ing.quantity" class="input !w-32" placeholder="Cantidad" aria-label="Cantidad" />
          <input v-model="ing.name" class="input" placeholder="Ingrediente" aria-label="Ingrediente" />
          <button type="button" class="btn-ghost !px-3" aria-label="Quitar" @click="form.ingredients.splice(i, 1)">✕</button>
        </div>
        <button type="button" class="btn-ghost" @click="form.ingredients.push({ name: '', quantity: '' })">+ Ingrediente</button>
      </fieldset>
      <fieldset class="space-y-2">
        <legend class="text-sm font-medium">Pasos</legend>
        <div v-for="(step, i) in form.steps" :key="i" class="flex gap-2">
          <span class="pt-2 text-sm text-muted">{{ i + 1 }}.</span>
          <textarea v-model="step.text" class="field" rows="2" :aria-label="`Paso ${i + 1}`" />
          <button type="button" class="btn-ghost !px-3" aria-label="Quitar" @click="form.steps.splice(i, 1)">✕</button>
        </div>
        <button type="button" class="btn-ghost" @click="form.steps.push({ text: '' })">+ Paso</button>
      </fieldset>
      <label class="block text-sm font-medium">Consejo de conservación<textarea v-model="form.storage_tip" class="field mt-1" rows="2" /></label>
      <div class="space-y-1">
        <p class="text-sm font-medium">Imagen (JPG, PNG o WEBP; se comprime antes de subir)</p>
        <ImageUploader :model-value="editing !== 'new' ? editing.image : null" shape="wide" @select="image = $event" />
      </div>
      <label class="block text-sm font-medium">Estado
        <select v-model="form.status" class="input mt-1 sm:max-w-xs">
          <option value="draft">Borrador</option>
          <option value="published" :disabled="!canApprove">Publicada{{ canApprove ? "" : " (requiere permiso de aprobar)" }}</option>
        </select>
      </label>
    </AdminModal>

    <ConfirmDialog
      :open="!!removeTarget" title="¿Eliminar la receta?" :description="removeTarget?.title" confirm-label="Eliminar" danger
      @cancel="removeTarget = null"
      @confirm="guard(async () => { await crud.remove(removeTarget!.id); removeTarget = null; })"
    />
  </div>
</template>
