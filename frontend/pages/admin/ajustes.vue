<script setup lang="ts">
import { siteSettingsService } from "~/services/site-settings.service";

// Ajustes generales del sitio: los cambia cualquier administradora, sin desplegar.
definePageMeta({ layout: "admin", middleware: "admin" });

const form = reactive({ access_whatsapp: "" });
const saving = ref(false);
const message = ref("");
const error = ref("");

const { data } = await siteSettingsService.get();
form.access_whatsapp = data.access_whatsapp;

const invalid = computed(() => form.access_whatsapp.trim() !== "" && !new RegExp(PHONE_PATTERN).test(form.access_whatsapp.trim()));
const whatsappLink = computed(() => {
  const digits = form.access_whatsapp.replace(/\D/g, "");
  return digits ? `https://wa.me/${digits}` : "";
});

async function save() {
  if (invalid.value) return;
  saving.value = true;
  message.value = error.value = "";
  try {
    const { data: saved } = await siteSettingsService.update({ access_whatsapp: form.access_whatsapp.trim() });
    form.access_whatsapp = saved.access_whatsapp;
    message.value = "Guardado. Ya se muestra en la pantalla de acceso pendiente.";
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="max-w-2xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Ajustes generales</h1>
      <p class="text-sm text-muted">Datos que se usan en todo el sitio. Los cambios quedan en el historial.</p>
    </header>

    <form class="card space-y-4 p-5" @submit.prevent="save">
      <label class="block">
        <span class="text-sm font-medium text-ink">WhatsApp para solicitar el acceso al grupo</span>
        <input v-model="form.access_whatsapp" class="field mt-1" placeholder="+57 300 000 0000" inputmode="tel" />
        <span class="mt-1 block text-xs text-muted">
          Es el número al que escriben las personas que se registran pero aún no pertenecen al grupo. Con el código de país
          (ej. +57). Déjalo vacío para ocultar el botón de WhatsApp.
        </span>
        <span v-if="invalid" class="mt-1 block text-xs text-rose-500">Escribe el número con el código de país, ej: +57 300 000 0000.</span>
      </label>
      <a v-if="whatsappLink && !invalid" :href="whatsappLink" target="_blank" rel="noopener" class="text-xs text-gold hover:underline">
        Probar enlace de WhatsApp
      </a>
      <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
      <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
      <button class="btn-primary" :disabled="saving || invalid">{{ saving ? "Guardando..." : "Guardar" }}</button>
    </form>
  </div>
</template>
