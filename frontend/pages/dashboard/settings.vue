<script setup lang="ts">
import { authService } from "~/services/auth.service";

definePageMeta({ layout: "dashboard" });

const authStore = useAuthStore();

const form = reactive({
  first_name: authStore.user?.first_name || "",
  last_name: authStore.user?.last_name || "",
});
const loading = ref(false);
const success = ref(false);
const error = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";
  success.value = false;
  try {
    await authStore.updateProfile({ ...form });
    success.value = true;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

const passwordForm = reactive({ current_password: "", new_password: "", confirm_password: "" });
const passwordLoading = ref(false);
const passwordSuccess = ref(false);
const passwordError = ref("");

async function handlePasswordSubmit() {
  passwordError.value = "";
  passwordSuccess.value = false;
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = "Las contraseñas nuevas no coinciden.";
    return;
  }
  passwordLoading.value = true;
  try {
    await authService.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
    passwordSuccess.value = true;
    passwordForm.current_password = "";
    passwordForm.new_password = "";
    passwordForm.confirm_password = "";
  } catch (err) {
    passwordError.value = useErrorMessage(err);
  } finally {
    passwordLoading.value = false;
  }
}
</script>

<template>
  <div class="max-w-4xl">
    <NuxtLink to="/" class="inline-flex items-center gap-2 text-sm font-medium text-muted transition hover:text-gold">
      <img src="/logo-mark.png" alt="Tribu Paridas" class="h-8 w-8" />
      Volver al inicio
    </NuxtLink>

    <h1 class="mt-4 text-2xl font-bold text-ink">Configuración</h1>
    <p class="mt-1 text-sm text-muted">Actualiza tus datos personales.</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
    <div class="card p-6">
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Email</label>
          <input :value="authStore.user?.email" type="email" disabled class="field bg-line/40 text-muted" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
            <input v-model="form.first_name" type="text" class="field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
            <input v-model="form.last_name" type="text" class="field" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">WhatsApp</label>
          <input :value="authStore.user?.whatsapp" type="text" disabled class="field bg-line/40 text-muted" />
          <p class="mt-1 text-xs text-muted">Para cambiar tu WhatsApp, contacta al equipo admin.</p>
        </div>
        <p v-if="success" class="text-sm text-emerald-600">Perfil actualizado.</p>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary" :disabled="loading">Guardar cambios</button>
      </form>
    </div>

    <div class="card p-6">
      <h2 class="text-lg font-semibold text-ink">Cambiar contraseña</h2>
      <form class="mt-4 space-y-4" @submit.prevent="handlePasswordSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña actual</label>
          <input v-model="passwordForm.current_password" type="password" required class="field" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña nueva</label>
          <input v-model="passwordForm.new_password" type="password" required minlength="8" class="field" placeholder="Mínimo 8 caracteres" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Confirmar contraseña nueva</label>
          <input v-model="passwordForm.confirm_password" type="password" required minlength="8" class="field" />
        </div>
        <p v-if="passwordSuccess" class="text-sm text-emerald-600">Contraseña actualizada.</p>
        <p v-if="passwordError" class="text-sm text-rose-500">{{ passwordError }}</p>
        <button type="submit" class="btn-primary" :disabled="passwordLoading">
          {{ passwordLoading ? "Guardando..." : "Cambiar contraseña" }}
        </button>
      </form>
    </div>
    </div>
  </div>
</template>
