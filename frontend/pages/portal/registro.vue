<script setup lang="ts">
import { portalService } from "~/services/portal.service";

// Alta de cuentas "solo portal": quedan inactivas hasta que un admin las aprueba y las asigna a un emprendimiento.
const flags = useFeatureFlagStore();
if (!flags.loaded) await flags.load();
if (!flags.isPortalLive) await navigateTo("/");

const form = reactive({ first_name: "", last_name: "", email: "", whatsapp: "", business_name: "", password: "" });
const loading = ref(false);
const error = ref("");
const done = ref("");

async function submit() {
  error.value = "";
  if (!new RegExp(PHONE_PATTERN).test(form.whatsapp.trim())) {
    error.value = PHONE_ERROR_MESSAGE;
    return;
  }
  if (form.password.length < 8) {
    error.value = "La contraseña debe tener al menos 8 caracteres.";
    return;
  }
  loading.value = true;
  try {
    done.value = (await portalService.registerPortal({ ...form })).data.detail;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex min-h-[70vh] max-w-md items-center px-4 py-10">
    <div class="card w-full space-y-4 p-6">
      <div class="text-center">
        <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="mx-auto h-14 w-14" />
        <h1 class="mt-2 text-2xl font-bold text-ink">Portal de emprendimientos</h1>
        <p class="text-sm text-muted">Pide acceso para gestionar tu emprendimiento y validar los descuentos de la tribu.</p>
      </div>

      <div v-if="done" class="space-y-3 text-center">
        <AppIcon name="check-circle" :size="36" class="mx-auto text-emerald-600" />
        <p class="text-sm text-ink">{{ done }}</p>
        <NuxtLink to="/login" class="btn-primary">Ir a iniciar sesión</NuxtLink>
      </div>

      <form v-else class="space-y-3" @submit.prevent="submit">
        <div class="grid grid-cols-2 gap-3">
          <input v-model="form.first_name" required class="field" placeholder="Nombre" aria-label="Nombre" />
          <input v-model="form.last_name" required class="field" placeholder="Apellido" aria-label="Apellido" />
        </div>
        <input v-model="form.email" type="email" required class="field" placeholder="Correo" aria-label="Correo" />
        <input v-model="form.whatsapp" required class="field" placeholder="+57 300 000 0000" aria-label="WhatsApp" />
        <input v-model="form.business_name" required class="field" placeholder="Nombre de tu emprendimiento" aria-label="Emprendimiento" />
        <input v-model="form.password" type="password" required minlength="8" class="field" placeholder="Contraseña (mín. 8)" aria-label="Contraseña" />
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? "Enviando..." : "Solicitar acceso" }}</button>
        <p class="text-center text-xs text-muted">Esta cuenta es solo para el portal. Si quieres usar todo el sitio, podrás pedir el cambio después.</p>
      </form>
    </div>
  </div>
</template>
