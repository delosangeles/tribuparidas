<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { CookbookAdmin, CatalogItem } from "~/types/alimentacion";

defineProps<{ ages: CatalogItem[] }>();

const MAX_PDF_MB = 10;
const authStore = useAuthStore();
const canAdd = computed(() => authStore.can("alimentacion", "add"));
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canApprove = computed(() => authStore.can("alimentacion", "approve"));
const canDelete = computed(() => authStore.can("alimentacion", "delete"));

const crud = useAdminCrud<CookbookAdmin>("recetarios");
await crud.load();

const blank = () => ({ title: "", summary: "", age_range: null as number | null, status: "draft" });
const editing = ref<CookbookAdmin | "new" | null>(null);
const form = reactive(blank());
const pdf = ref<File | null>(null);
const image = ref<File | null>(null);
const saving = ref(false);
const formError = ref("");
const actionError = ref("");
const removeTarget = ref<CookbookAdmin | null>(null);

const hasPdf = computed(() => Boolean(pdf.value || (editing.value && editing.value !== "new" && editing.value.pdf)));

function open(item?: CookbookAdmin) {
  Object.assign(form, item ? { title: item.title, summary: item.summary, age_range: item.age_range, status: item.status } : blank());
  pdf.value = null;
  image.value = null;
  formError.value = "";
  editing.value = item ?? "new";
}

function onPdf(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null;
  formError.value = "";
  if (file && file.size > MAX_PDF_MB * 1024 * 1024) {
    formError.value = `El PDF no puede superar ${MAX_PDF_MB}MB.`;
    (event.target as HTMLInputElement).value = "";
    pdf.value = null;
    return;
  }
  pdf.value = file;
}

async function save() {
  saving.value = true;
  formError.value = "";
  try {
    const api = alimentacionService.admin;
    const id = editing.value === "new" ? null : (editing.value as CookbookAdmin).id;
    const wantsPublish = form.status === "published";
    // Se guarda como borrador, se sube el PDF y recién entonces se publica (el servidor exige el PDF).
    const payload = { ...form, status: "draft" };
    let saved = (id ? await api.update<CookbookAdmin>("recetarios", id, payload) : await api.create<CookbookAdmin>("recetarios", payload)).data;
    if (pdf.value) saved = (await api.uploadPdf(saved.id, pdf.value)).data;
    if (image.value) saved = (await api.uploadImage<CookbookAdmin>("recetarios", saved.id, image.value)).data;
    if (wantsPublish) await api.publish<CookbookAdmin>("recetarios", saved.id);
    await crud.load();
    editing.value = null;
  } catch (err) {
    formError.value = useErrorMessage(err);
    await crud.load();
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
    <div class="flex justify-end"><button v-if="canAdd" class="btn-primary" @click="open()">Nuevo recetario</button></div>
    <p v-if="actionError || crud.error.value" class="rounded-xl2 bg-rose-50 px-3 py-2 text-sm text-rose-600">{{ actionError || crud.error.value }}</p>
    <ul class="space-y-2">
      <li v-for="(item, index) in crud.items.value" :key="item.id" class="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div class="min-w-0 space-y-1">
          <p class="font-semibold text-ink">{{ item.title }}</p>
          <div class="flex flex-wrap items-center gap-2">
            <span :class="item.status === 'published' ? 'badge-approved' : 'badge-pending'">{{ item.status === "published" ? "Publicado" : "Borrador" }}</span>
            <span v-if="!item.pdf" class="text-xs text-rose-600">Falta el PDF</span>
          </div>
        </div>
        <RowActions
          :index="index" :total="crud.items.value.length" :status="item.status"
          :preview-to="`/alimentacion-complementaria/recetarios/${item.slug}?preview=1`"
          :can-edit="canEdit" :can-approve="canApprove" :can-delete="canDelete"
          @move="guard(() => crud.move(index, $event))"
          @toggle="guard(() => crud.setPublished(item, item.status !== 'published'))"
          @edit="open(item)" @remove="removeTarget = item"
        />
      </li>
    </ul>
    <EmptyState v-if="!crud.items.value.length && !crud.loading.value" icon="file-text" title="Todavía no hay recetarios en PDF" />

    <AdminModal v-if="editing" :title="editing === 'new' ? 'Nuevo recetario' : 'Editar recetario'" :saving="saving" :error="formError" @save="save" @cancel="editing = null">
      <label class="block text-sm font-medium">Título<input v-model="form.title" class="input mt-1" required maxlength="200" /></label>
      <label class="block text-sm font-medium">Descripción<textarea v-model="form.summary" class="field mt-1" rows="2" /></label>
      <label class="block text-sm font-medium">Categoría de edad
        <select v-model="form.age_range" class="input mt-1 sm:max-w-xs">
          <option :value="null">Sin categoría</option>
          <option v-for="a in ages" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
      </label>
      <div class="space-y-1">
        <p class="text-sm font-medium">Archivo PDF (máx. {{ MAX_PDF_MB }}MB)</p>
        <p v-if="editing !== 'new' && editing.pdf" class="text-xs text-muted">
          Ya hay un PDF cargado (<a :href="editing.pdf" target="_blank" class="text-gold-dark underline">verlo</a>). Elige otro solo si quieres reemplazarlo.
        </p>
        <input type="file" accept="application/pdf,.pdf" class="block w-full text-sm" @change="onPdf" />
      </div>
      <div class="space-y-1">
        <p class="text-sm font-medium">Portada (opcional)</p>
        <ImageUploader :model-value="editing !== 'new' ? editing.image : null" shape="wide" @select="image = $event" />
      </div>
      <label class="block text-sm font-medium">Estado
        <select v-model="form.status" class="input mt-1 sm:max-w-xs">
          <option value="draft">Borrador</option>
          <option value="published" :disabled="!canApprove || !hasPdf">
            Publicado{{ !canApprove ? " (requiere permiso de aprobar)" : !hasPdf ? " (sube el PDF primero)" : "" }}
          </option>
        </select>
      </label>
    </AdminModal>

    <ConfirmDialog
      :open="!!removeTarget" title="¿Eliminar el recetario?" :description="removeTarget?.title" confirm-label="Eliminar" danger
      @cancel="removeTarget = null"
      @confirm="guard(async () => { await crud.remove(removeTarget!.id); removeTarget = null; })"
    />
  </div>
</template>
