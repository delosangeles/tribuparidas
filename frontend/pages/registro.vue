<script setup lang="ts">
const authStore = useAuthStore();

const form = reactive({
  first_name: "",
  last_name: "",
  email: "",
  whatsapp: "",
  password: "",
});

const loading = ref(false);
const error = ref("");
const submitted = ref(false);
const registerMessage = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";

  try {
    const data = await authStore.register({ ...form });

    registerMessage.value = data.detail;
    submitted.value = true;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto flex min-h-[80vh] max-w-md flex-col items-center px-4 py-16">
    <NuxtLink to="/login">
      <BrandMark />
    </NuxtLink>

    <div class="mt-4 text-center">
      <h1 class="text-2xl font-bold text-ink">
        Bienvenida a la tribu
      </h1>

      <p class="mt-1 text-sm text-muted">
        Crea tu cuenta para comenzar.
      </p>
    </div>

    <div v-if="submitted" class="card mt-8 w-full p-6 text-center">
      <span
        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500"
      >
        <AppIcon name="check-circle" :size="26" />
      </span>

      <p class="mt-4 font-semibold text-ink">
        ¡Registro recibido!
      </p>

      <p class="mt-1 text-sm text-muted">
        {{ registerMessage }}
      </p>

      <NuxtLink to="/login" class="btn-outline mt-4 inline-flex">
        Iniciar sesión
      </NuxtLink>
    </div>

    <div v-else class="card mt-8 w-full p-6">
      <form class="space-y-4" @submit.prevent="handleSubmit">

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              Nombre
            </label>

            <input
              v-model="form.first_name"
              type="text"
              required
              class="field"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              Apellido
            </label>

            <input
              v-model="form.last_name"
              type="text"
              required
              class="field"
            />
          </div>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Correo
          </label>

          <input
            v-model="form.email"
            type="email"
            required
            class="field"
            placeholder="tu@email.com"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            WhatsApp
          </label>

          <input
            v-model="form.whatsapp"
            type="text"
            required
            :pattern="PHONE_PATTERN"
            :title="PHONE_ERROR_MESSAGE"
            class="field"
            placeholder="+57 300 000 0000"
          />

          <p class="mt-1 text-xs text-muted">
            Con este número confirmamos que estás en el grupo de la tribu.
          </p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Contraseña
          </label>

          <input
            v-model="form.password"
            type="password"
            required
            minlength="8"
            class="field"
            placeholder="Mínimo 8 caracteres"
          />
        </div>

        <p v-if="error" class="text-sm text-rose-500">
          {{ error }}
        </p>

        <button
          type="submit"
          class="btn-primary w-full"
          :disabled="loading"
        >
          {{ loading ? "Enviando..." : "Registrarme" }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-muted">
        ¿Ya tienes cuenta?
        <NuxtLink
          to="/login"
          class="font-semibold text-gold hover:underline"
        >
          Inicia sesión
        </NuxtLink>
      </p>
    </div>
  </div>
</template>