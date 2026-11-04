<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import { siteSettingsService } from "~/services/site-settings.service";
import { toFormData } from "~/services/utils";
import type { BusinessFormPayload } from "~/types";
import { reviewWhatsappUrl } from "~/utils/whatsapp";

// Alta de una emprendedora en dos pasos: 1) sus datos, 2) los datos mínimos de su emprendimiento.
// La cuenta queda activa de una vez (ve lo público, no lo privado de la tribu) y el emprendimiento
// queda en espera de aprobación (1 a 2 días hábiles) con todos sus datos ya cargados.
const flags = useFeatureFlagStore();
const authStore = useAuthStore();
const portalStore = usePortalStore();
if (!flags.loaded) await flags.load();
if (!flags.isPortalLive) await navigateTo("/");

const step = ref<1 | 2>(1);
const person = reactive({ first_name: "", last_name: "", email: "", whatsapp: "", password: "" });
const loading = ref(false);
const error = ref("");
const done = ref<{ businessName: string } | null>(null);
const teamWhatsapp = ref("");

function nextStep() {
  error.value = "";
  if (!person.first_name.trim() || !person.last_name.trim() || !person.email.trim()) {
    error.value = "Completa tu nombre, apellido y correo.";
    return;
  }
  if (!new RegExp(PHONE_PATTERN).test(person.whatsapp.trim())) {
    error.value = PHONE_ERROR_MESSAGE;
    return;
  }
  if (person.password.length < 8) {
    error.value = "La contraseña debe tener al menos 8 caracteres.";
    return;
  }
  step.value = 2;
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

async function submit(payload: BusinessFormPayload) {
  error.value = "";
  loading.value = true;
  try {
    const business = Object.fromEntries(Object.entries(payload).map(([key, value]) => [`business_${key}`, value]));
    const { data } = await portalService.registerPortal(
      toFormData({
        ...person,
        first_name: person.first_name.trim(),
        last_name: person.last_name.trim(),
        email: person.email.trim(),
        whatsapp: person.whatsapp.trim(),
        ...business,
      })
    );
    // Entra de una vez: se inicia la sesión con lo que devuelve el registro.
    authStore.setSession({ access: data.access, refresh: data.refresh, user: data.user });
    portalStore.reset();
    await flags.load();
    try {
      teamWhatsapp.value = (await siteSettingsService.get()).data.access_whatsapp;
    } catch {
      // sin número configurado: solo se muestra el mensaje
    }
    done.value = { businessName: data.business.name };
  } catch (err) {
    error.value = useErrorMessage(err);
    // Si el problema es de la cuenta (ej. correo repetido), se vuelve al paso 1.
    const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
    if (data && ["email", "password", "first_name", "last_name", "whatsapp"].some((field) => field in data)) step.value = 1;
  } finally {
    loading.value = false;
  }
}

const whatsappUrl = computed(() =>
  done.value
    ? reviewWhatsappUrl(teamWhatsapp.value, done.value.businessName, `${person.first_name} ${person.last_name}`.trim(), person.email.trim())
    : ""
);
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8 sm:py-10">
    <div class="card w-full space-y-5 p-5 sm:p-6">
      <div class="text-center">
        <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="mx-auto h-14 w-14" />
        <h1 class="mt-2 text-2xl font-bold text-ink">Registra tu emprendimiento</h1>
        <p v-if="!done" class="text-sm text-muted">Crea tu cuenta y publica tu emprendimiento en la tribu. Son dos pasos.</p>
      </div>

      <!-- Listo -->
      <div v-if="done" class="space-y-4 text-center">
        <AppIcon name="check-circle" :size="40" class="mx-auto text-emerald-600" />
        <p class="text-lg font-semibold text-ink">¡Listo! «{{ done.businessName }}» quedó en espera</p>
        <p class="text-sm text-ink">
          Tu emprendimiento será revisado en <strong>1 o 2 días hábiles</strong>. Mientras tanto ya puedes entrar a tu portal y completar su información.
        </p>
        <p v-if="whatsappUrl" class="text-sm text-muted">Si necesitas cualquier información o quieres que lo revisemos pronto, escríbenos:</p>
        <a v-if="whatsappUrl" :href="whatsappUrl" target="_blank" rel="noopener" class="btn-outline mx-auto flex w-full max-w-xs justify-center">
          <AppIcon name="whatsapp" :size="16" /> Escribir por WhatsApp
        </a>
        <NuxtLink to="/portal" class="btn-primary mx-auto flex w-full max-w-xs justify-center">Entrar a mi portal</NuxtLink>
      </div>

      <template v-else>
        <!-- Pasos -->
        <ol class="flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-semibold sm:gap-2 sm:text-sm" aria-label="Pasos del registro">
          <li>
            <button
              type="button"
              class="rounded-full border px-3 py-1.5 transition sm:px-4"
              :class="step === 1 ? 'border-gold bg-gold-light text-gold' : 'border-line text-muted hover:text-gold'"
              :aria-current="step === 1 ? 'step' : undefined"
              @click="step = 1"
            >
              1. Tus datos
            </button>
          </li>
          <li class="text-muted" aria-hidden="true">→</li>
          <li>
            <span class="rounded-full border px-3 py-1.5 sm:px-4" :class="step === 2 ? 'border-gold bg-gold-light text-gold' : 'border-line text-muted'" :aria-current="step === 2 ? 'step' : undefined">
              2. Tu emprendimiento
            </span>
          </li>
        </ol>

        <!-- Paso 1: la persona -->
        <form v-show="step === 1" class="mx-auto max-w-md space-y-3" @submit.prevent="nextStep">
          <div class="grid grid-cols-2 gap-3">
            <input v-model="person.first_name" required class="field" placeholder="Nombre" aria-label="Nombre" autocomplete="given-name" />
            <input v-model="person.last_name" required class="field" placeholder="Apellido" aria-label="Apellido" autocomplete="family-name" />
          </div>
          <input v-model="person.email" type="email" required class="field" placeholder="Correo" aria-label="Correo" autocomplete="email" />
          <input v-model="person.whatsapp" required class="field" placeholder="Tu WhatsApp: +57 300 000 0000" aria-label="WhatsApp" autocomplete="tel" />
          <input v-model="person.password" type="password" required minlength="8" class="field" placeholder="Contraseña (mín. 8)" aria-label="Contraseña" autocomplete="new-password" />
          <p v-if="error && step === 1" class="text-sm text-rose-500" role="alert">{{ error }}</p>
          <button class="btn-primary w-full">Siguiente: mi emprendimiento →</button>
          <p class="text-center text-sm text-muted">
            ¿Ya tienes cuenta? <NuxtLink to="/login" class="font-semibold text-gold hover:underline">Inicia sesión</NuxtLink>
          </p>
        </form>

        <!-- Paso 2: el emprendimiento (datos mínimos) -->
        <div v-if="step === 2" class="space-y-4">
          <div class="rounded-xl2 bg-gold-light/50 p-3 text-sm text-ink">
            <p class="font-semibold">Datos mínimos para publicarlo</p>
            <p class="mt-0.5 text-muted">
              Necesitamos el nombre, el logo, la descripción, la categoría, la ubicación y un WhatsApp de contacto. Lo demás es opcional y lo puedes completar después desde tu portal.
            </p>
          </div>
          <p v-if="error" class="text-sm text-rose-500" role="alert">{{ error }}</p>
          <BusinessForm submit-label="Crear mi emprendimiento" :loading="loading" minimal-required @submit="submit" />
          <button type="button" class="btn-ghost w-full" :disabled="loading" @click="step = 1">← Volver a mis datos</button>
          <p class="text-center text-xs text-muted">
            Tu emprendimiento quedará en espera de aprobación (1 o 2 días hábiles). Con tu cuenta ves todo lo público, pero no lo privado de la tribu.
          </p>
        </div>
      </template>
    </div>
  </div>
</template>
