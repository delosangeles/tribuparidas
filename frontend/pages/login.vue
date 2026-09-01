<script setup lang="ts">
import { authService } from "~/services/auth.service";

const authStore = useAuthStore();
const route = useRoute();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";
  try {
    await authStore.login(email.value, password.value);
    const redirect = (route.query.redirect as string) || (authStore.isAdmin ? "/admin" : "/");
    navigateTo(redirect);
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

const showForgot = ref(false);
const forgotEmail = ref("");
const forgotLoading = ref(false);
const forgotSent = ref(false);
const forgotError = ref("");

function openForgot() {
  forgotEmail.value = email.value;
  forgotSent.value = false;
  forgotError.value = "";
  showForgot.value = true;
}

async function submitForgot() {
  forgotLoading.value = true;
  forgotError.value = "";
  try {
    await authService.requestPasswordReset(forgotEmail.value);
    forgotSent.value = true;
  } catch (err) {
    forgotError.value = useErrorMessage(err);
  } finally {
    forgotLoading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col items-center px-4 py-16">
    <NuxtLink to="/">
      <BrandMark />
    </NuxtLink>

    <div class="card mt-8 w-full p-6">
      <h1 class="text-xl font-bold text-ink">Iniciar sesión</h1>
      <p class="mt-1 text-sm text-muted">Bienvenida de nuevo a la comunidad.</p>

      <form class="mt-6 space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Email</label>
          <input v-model="email" type="email" required class="field" placeholder="tu@email.com" />
        </div>
        <div>
          <div class="mb-1 flex items-center justify-between">
            <label class="block text-sm font-medium text-ink">Contraseña</label>
            <button type="button" class="text-xs font-semibold text-gold hover:underline" @click="openForgot">
              ¿La olvidaste?
            </button>
          </div>
          <input v-model="password" type="password" required class="field" placeholder="••••••••" />
        </div>
        <div v-if="error">
          <p class="text-sm text-rose-500">{{ error }}</p>
          <p class="mt-1 text-xs text-muted">Si te acabas de registrar, tu cuenta puede estar en revisión.</p>
        </div>
        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? "Ingresando..." : "Iniciar sesión" }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-muted">
        ¿No tienes cuenta?
        <NuxtLink to="/" class="font-semibold text-gold hover:underline">Regístrate</NuxtLink>
      </p>
    </div>

    <Teleport to="body">
      <div v-if="showForgot" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <template v-if="forgotSent">
            <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500">
              <AppIcon name="check-circle" :size="24" />
            </span>
            <p class="mt-4 text-center font-semibold text-ink">¡Listo!</p>
            <p class="mt-1 text-center text-sm text-muted">
              Le avisamos al equipo. Te contactarán por WhatsApp para ayudarte a recuperar el acceso.
            </p>
            <button class="btn-primary mt-6 w-full" @click="showForgot = false">Cerrar</button>
          </template>
          <template v-else>
            <p class="text-lg font-semibold text-ink">¿Olvidaste tu contraseña?</p>
            <p class="mt-1 text-sm text-muted">
              Escribe tu correo. Le avisamos al equipo de la tribu para que te ayude a recuperar el acceso por WhatsApp.
            </p>
            <form class="mt-4 space-y-3" @submit.prevent="submitForgot">
              <input v-model="forgotEmail" type="email" required class="field" placeholder="tu@email.com" />
              <p v-if="forgotError" class="text-sm text-rose-500">{{ forgotError }}</p>
              <div class="flex justify-end gap-2">
                <button type="button" class="btn-ghost" @click="showForgot = false">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="forgotLoading">
                  {{ forgotLoading ? "Enviando..." : "Avisar al equipo" }}
                </button>
              </div>
            </form>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>
