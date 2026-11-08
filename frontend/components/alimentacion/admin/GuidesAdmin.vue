<script setup lang="ts">
import type { GuideAdmin } from "~/types/alimentacion";

const authStore = useAuthStore();
const canAdd = computed(() => authStore.can("alimentacion", "add"));
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canApprove = computed(() => authStore.can("alimentacion", "approve"));
const canDelete = computed(() => authStore.can("alimentacion", "delete"));

const crud = useAdminCrud<GuideAdmin>("guias");
await crud.load();

const editing = ref<GuideAdmin | "new" | null>(null);
const form = reactive({ title: "", summary: "", content: "", status: "draft" });
const image = ref<File | null>(null);
const saving = ref(false);
const formError = ref("");
const actionError = ref("");
const removeTarget = ref<GuideAdmin | null>(null);

function open(guide?: GuideAdmin) {
  Object.assign(form, guide ? { title: guide.title, summary: guide.summary, content: guide.content, status: guide.status } : { title: "", summary: "", content: "", status: "draft" });
  image.value = null;
  formError.value = "";
  editing.value = guide ?? "new";
}
async function save() {
  saving.value = true;
  formError.value = "";
  try {
    await crud.save({ ...form }, editing.value === "new" ? null : (editing.value as GuideAdmin).id, image.value);
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
    <div class="flex justify-end"><button v-if="canAdd" class="btn-primary" @click="open()">Nueva guía</button></div>
    <p v-if="actionError || crud.error.value" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ actionError || crud.error.value }}</p>
    <ul class="space-y-2">
      <li v-for="(item, index) in crud.items.value" :key="item.id" class="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div class="min-w-0">
          <p class="font-semibold text-ink">{{ item.title }}</p>
          <span :class="item.status === 'published' ? 'badge-approved' : 'badge-pending'">{{ item.status === "published" ? "Publicada" : "Borrador" }}</span>
        </div>
        <RowActions
          :index="index" :total="crud.items.value.length" :status="item.status"
          :preview-to="`/alimentacion-complementaria/guias/${item.slug}?preview=1`"
          :can-edit="canEdit" :can-approve="canApprove" :can-delete="canDelete"
          @move="guard(() => crud.move(index, $event))"
          @toggle="guard(() => crud.setPublished(item, item.status !== 'published'))"
          @edit="open(item)" @remove="removeTarget = item"
        />
      </li>
    </ul>
    <EmptyState v-if="!crud.items.value.length && !crud.loading.value" icon="file-text" title="Todavía no hay guías" />

    <AdminModal v-if="editing" :title="editing === 'new' ? 'Nueva guía' : 'Editar guía'" :saving="saving" :error="formError" @save="save" @cancel="editing = null">
      <label class="block text-sm font-medium">Título<input v-model="form.title" class="input mt-1" required maxlength="200" /></label>
      <label class="block text-sm font-medium">Resumen<textarea v-model="form.summary" class="field mt-1" rows="2" /></label>
      <div class="space-y-1">
        <p class="text-sm font-medium">Contenido</p>
        <RichTextEditor v-model="form.content" />
      </div>
      <div class="space-y-1">
        <p class="text-sm font-medium">Imagen</p>
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
      :open="!!removeTarget" title="¿Eliminar la guía?" :description="removeTarget?.title" confirm-label="Eliminar" danger
      @cancel="removeTarget = null"
      @confirm="guard(async () => { await crud.remove(removeTarget!.id); removeTarget = null; })"
    />
  </div>
</template>
