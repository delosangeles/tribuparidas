<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { SafetyAdmin } from "~/types/alimentacion";

const authStore = useAuthStore();
const canEdit = computed(() => authStore.can("alimentacion", "edit"));
const canApprove = computed(() => authStore.can("alimentacion", "approve"));

const form = reactive<SafetyAdmin>({ content: "", professional_name: "", professional_title: "", reviewed_on: null, status: "draft" });
const message = ref("");
const error = ref("");
const saving = ref(false);

try {
  Object.assign(form, (await alimentacionService.admin.safety()).data);
} catch (err) {
  error.value = useErrorMessage(err);
}

async function save() {
  saving.value = true;
  message.value = error.value = "";
  try {
    const payload = { ...form, reviewed_on: form.reviewed_on || null };
    Object.assign(form, (await alimentacionService.admin.saveSafety(payload)).data);
    message.value = "Guardado.";
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <form class="card space-y-4 p-5" @submit.prevent="save">
    <p class="text-sm text-muted">
      Sección fija: atragantamiento vs. arcadas, alimentos que no se deben dar y qué hacer ante una reacción alérgica.
      Debe redactarla y firmarla un profesional; no se publica sin nombre y firma.
    </p>
    <RichTextEditor v-model="form.content" />
    <div class="grid gap-3 sm:grid-cols-3">
      <label class="block text-sm font-medium">Nombre del profesional<input v-model="form.professional_name" class="input mt-1" maxlength="150" /></label>
      <label class="block text-sm font-medium">Cargo o especialidad<input v-model="form.professional_title" class="input mt-1" maxlength="150" /></label>
      <label class="block text-sm font-medium">Fecha de revisión<input v-model="form.reviewed_on" type="date" class="input mt-1" /></label>
    </div>
    <label class="block text-sm font-medium">Estado
      <select v-model="form.status" class="input mt-1 sm:max-w-xs" :disabled="!canApprove && form.status !== 'draft'">
        <option value="draft">Borrador (no se muestra)</option>
        <option value="published" :disabled="!canApprove || !form.professional_name || !form.content">Publicada</option>
      </select>
    </label>
    <div class="flex flex-wrap items-center gap-3">
      <button class="btn-primary" :disabled="saving || !canEdit">{{ saving ? "Guardando…" : "Guardar" }}</button>
      <NuxtLink to="/alimentacion-complementaria?seccion=seguridad&preview=1" target="_blank" class="btn-ghost">Vista previa</NuxtLink>
      <span v-if="message" class="text-sm text-emerald-600">{{ message }}</span>
      <span v-if="error" class="text-sm text-rose-600">{{ error }}</span>
    </div>
  </form>
</template>
