<script setup lang="ts">
import type { CatalogItem, FoodAdmin } from "~/types/alimentacion";

defineProps<{ ages: CatalogItem[]; allergens: CatalogItem[] }>();

const authStore = useAuthStore();
const canAdd = computed(() => authStore.can("alimentacion", "add"));
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canApprove = computed(() => authStore.can("alimentacion", "approve"));
const canDelete = computed(() => authStore.can("alimentacion", "delete"));

const crud = useAdminCrud<FoodAdmin>("alimentos");
await crud.load();

const blank = () => ({ name: "", age_range: null as number | null, how_to_offer: "", is_common_allergen: false, allergen: null as number | null, status: "draft" });
const editing = ref<FoodAdmin | "new" | null>(null);
const form = reactive(blank());
const saving = ref(false);
const formError = ref("");
const actionError = ref("");
const removeTarget = ref<FoodAdmin | null>(null);

function open(food?: FoodAdmin) {
  Object.assign(form, food ? { name: food.name, age_range: food.age_range, how_to_offer: food.how_to_offer, is_common_allergen: food.is_common_allergen, allergen: food.allergen, status: food.status } : blank());
  formError.value = "";
  editing.value = food ?? "new";
}
async function save() {
  saving.value = true;
  formError.value = "";
  try {
    await crud.save({ ...form }, editing.value === "new" ? null : (editing.value as FoodAdmin).id);
    editing.value = null;
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}
async function guard(fn: () => Promise<unknown>) {
  actionError.value = "";
  try { await fn(); } catch (err) { actionError.value = useErrorMessage(err); }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex justify-end"><button v-if="canAdd" class="btn-primary" @click="open()">Nuevo alimento</button></div>
    <p v-if="actionError || crud.error.value" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ actionError || crud.error.value }}</p>
    <ul class="space-y-2">
      <li v-for="(item, index) in crud.items.value" :key="item.id" class="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div class="min-w-0">
          <p class="font-semibold text-ink">{{ item.name }}<span v-if="item.is_common_allergen" class="badge ml-2 bg-rose-50 text-rose-600">Alérgeno frecuente</span></p>
          <span :class="item.status === 'published' ? 'badge-approved' : 'badge-pending'">{{ item.status === "published" ? "Publicado" : "Borrador" }}</span>
        </div>
        <RowActions
          :index="index" :total="crud.items.value.length" :status="item.status"
          :can-edit="canEdit" :can-approve="canApprove" :can-delete="canDelete"
          @move="guard(() => crud.move(index, $event))"
          @toggle="guard(() => crud.setPublished(item, item.status !== 'published'))"
          @edit="open(item)" @remove="removeTarget = item"
        />
      </li>
    </ul>
    <EmptyState v-if="!crud.items.value.length && !crud.loading.value" icon="leaf" title="Todavía no hay alimentos" />

    <AdminModal v-if="editing" :title="editing === 'new' ? 'Nuevo alimento' : 'Editar alimento'" :saving="saving" :error="formError" @save="save" @cancel="editing = null">
      <label class="block text-sm font-medium">Nombre<input v-model="form.name" class="input mt-1" required maxlength="150" /></label>
      <label class="block text-sm font-medium">Edad sugerida de introducción
        <select v-model="form.age_range" class="input mt-1 sm:max-w-xs">
          <option :value="null">Sin definir</option>
          <option v-for="a in ages" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </label>
      <label class="block text-sm font-medium">Cómo ofrecerlo (forma y textura)<textarea v-model="form.how_to_offer" class="field mt-1" rows="3" /></label>
      <label class="flex items-center gap-2 text-sm font-medium"><input v-model="form.is_common_allergen" type="checkbox" /> Es alérgeno frecuente</label>
      <label v-if="form.is_common_allergen" class="block text-sm font-medium">Alérgeno del catálogo
        <select v-model="form.allergen" class="input mt-1 sm:max-w-xs">
          <option :value="null">Ninguno en particular</option>
          <option v-for="al in allergens" :key="al.id" :value="al.id">{{ al.name }}</option>
        </select>
      </label>
      <label class="block text-sm font-medium">Estado
        <select v-model="form.status" class="input mt-1 sm:max-w-xs">
          <option value="draft">Borrador</option>
          <option value="published" :disabled="!canApprove">Publicado{{ canApprove ? "" : " (requiere permiso de aprobar)" }}</option>
        </select>
      </label>
    </AdminModal>

    <ConfirmDialog
      :open="!!removeTarget" title="¿Eliminar el alimento?" :description="removeTarget?.name" confirm-label="Eliminar" danger
      @cancel="removeTarget = null"
      @confirm="guard(async () => { await crud.remove(removeTarget!.id); removeTarget = null; })"
    />
  </div>
</template>
