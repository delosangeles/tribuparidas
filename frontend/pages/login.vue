<script setup lang="ts">
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
    const redirect = (route.query.redirect as string) || (authStore.isAdmin ? "/admin" : "/dashboard");
    navigateTo(redirect);
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex max-w-md flex-col items-center px-4 py-16">
    <NuxtLink to="/" class="flex items-center gap-2 text-lg font-bold text-ink">
      <span class="flex h-8 w-8 items-center justify-center rounded-full bg-pink text-white">
        <AppIcon name="heart-filled" :size="16" />
      </span>
      Tribu Paridas
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
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña</label>
          <input v-model="password" type="password" required class="field" placeholder="••••••••" />
        </div>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? "Ingresando..." : "Iniciar sesión" }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-muted">
        ¿No tienes cuenta?
        <NuxtLink to="/registro" class="font-semibold text-pink hover:underline">Regístrate</NuxtLink>
      </p>
    </div>
  </div>
</template>
