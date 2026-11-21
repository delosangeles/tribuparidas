<script setup lang="ts">
import { siteSettingsService } from "~/services/site-settings.service";

// Ajustes generales del sitio: los cambia cualquier administradora, sin desplegar.
definePageMeta({ layout: "admin", middleware: "admin" });

const form = reactive({ access_whatsapp: "" });
const externalEnabled = ref(false);
const externalSaving = ref(false);
const externalMessage = ref("");
const saving = ref(false);
const message = ref("");
const error = ref("");

const { data } = await siteSettingsService.get();
form.access_whatsapp = data.access_whatsapp;
externalEnabled.value = data.external_discount_enabled === "1";

async function toggleExternal() {
  externalSaving.value = true;
  externalMessage.value = error.value = "";
  const next = !externalEnabled.value;
  try {
    const { data: saved } = await siteSettingsService.update({ external_discount_enabled: next ? "1" : "0" });
    externalEnabled.value = saved.external_discount_enabled === "1";
    externalMessage.value = externalEnabled.value ? "Activado: el lector de QR ya ofrece la opción." : "Desactivado: la opción desapareció del lector.";
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    externalSaving.value = false;
  }
}

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

    <section class="card space-y-3 p-5">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="font-semibold text-ink">Descuento a cliente externo</h2>
          <p class="mt-1 text-xs text-muted">
            Muestra en el lector de QR del portal la opción «Aplicar descuento a cliente externo», para personas sin cuenta (se pide solo
            nombre y apellido). Aplica el beneficio vigente del emprendimiento y queda en el historial.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="externalEnabled"
          :disabled="externalSaving"
          class="relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50"
          :class="externalEnabled ? 'bg-gold' : 'bg-line'"
          aria-label="Activar descuento a cliente externo"
          @click="toggleExternal"
        >
          <span class="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform" :class="externalEnabled && 'translate-x-5'" />
        </button>
      </div>
      <p class="text-xs font-medium" :class="externalEnabled ? 'text-emerald-600' : 'text-muted'">{{ externalEnabled ? "Activo" : "Desactivado" }}</p>
      <p v-if="externalMessage" class="text-sm text-emerald-600">{{ externalMessage }}</p>
    </section>
  </div>
</template>
