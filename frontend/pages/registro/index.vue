<script setup lang="ts">
const authStore = useAuthStore();

const form = reactive({ first_name: "", last_name: "", email: "", password: "" });
const loading = ref(false);
const error = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";
  try {
    await authStore.register({ ...form });
    navigateTo("/dashboard");
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
      <h1 class="text-xl font-bold text-ink">Crea tu cuenta</h1>
      <p class="mt-1 text-sm text-muted">Únete a la comunidad de Tribu Paridas.</p>

      <form class="mt-6 space-y-4" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
            <input v-model="form.first_name" type="text" required class="field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
            <input v-model="form.last_name" type="text" required class="field" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Email</label>
          <input v-model="form.email" type="email" required class="field" placeholder="tu@email.com" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña</label>
          <input v-model="form.password" type="password" required minlength="8" class="field" placeholder="Mínimo 8 caracteres" />
        </div>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? "Creando cuenta..." : "Crear cuenta" }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-muted">
        ¿Tienes un emprendimiento?
        <NuxtLink to="/registro/emprendimiento" class="font-semibold text-pink hover:underline">Regístralo aquí</NuxtLink>
      </p>
      <p class="mt-2 text-center text-sm text-muted">
        ¿Ya tienes cuenta?
        <NuxtLink to="/login" class="font-semibold text-pink hover:underline">Inicia sesión</NuxtLink>
      </p>
    </div>
  </div>
</template>
