<script setup lang="ts">
const authStore = useAuthStore();
const businessStore = useBusinessStore();

// Paso 1: si no hay sesión, primero se crea la cuenta.
const accountForm = reactive({ first_name: "", last_name: "", email: "", password: "" });
const accountLoading = ref(false);
const accountError = ref("");

async function handleAccountSubmit() {
  accountLoading.value = true;
  accountError.value = "";
  try {
    await authStore.register({ ...accountForm });
  } catch (err) {
    accountError.value = useErrorMessage(err);
  } finally {
    accountLoading.value = false;
  }
}

// Paso 2: una vez con sesión, se crea el emprendimiento.
const businessLoading = ref(false);
const businessError = ref("");
const created = ref(false);

async function handleBusinessSubmit(payload: any) {
  businessLoading.value = true;
  businessError.value = "";
  try {
    await businessStore.createBusiness(payload);
    created.value = true;
  } catch (err) {
    businessError.value = useErrorMessage(err);
  } finally {
    businessLoading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-12 sm:px-6">
    <div class="text-center">
      <h1 class="text-2xl font-bold text-ink">Registra tu emprendimiento</h1>
      <p class="mt-1 text-sm text-muted">Cuéntale a la comunidad qué estás construyendo.</p>
    </div>

    <div v-if="created" class="card mx-auto mt-8 max-w-md p-6 text-center">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500">
        <AppIcon name="check-circle" :size="26" />
      </span>
      <p class="mt-4 font-semibold text-ink">¡Tu emprendimiento fue enviado!</p>
      <p class="mt-1 text-sm text-muted">
        Nuestro equipo lo revisará antes de publicarlo. Puedes seguir el estado desde tu panel.
      </p>
      <NuxtLink to="/dashboard" class="btn-primary mt-4 inline-flex">Ir a mi panel</NuxtLink>
    </div>

    <div v-else-if="!authStore.isAuthenticated" class="card mx-auto mt-8 max-w-md p-6">
      <p class="text-sm font-semibold text-ink">Primero crea tu cuenta</p>
      <form class="mt-4 space-y-4" @submit.prevent="handleAccountSubmit">
        <div class="grid grid-cols-2 gap-3">
          <input v-model="accountForm.first_name" type="text" placeholder="Nombre" required class="field" />
          <input v-model="accountForm.last_name" type="text" placeholder="Apellido" required class="field" />
        </div>
        <input v-model="accountForm.email" type="email" placeholder="Email" required class="field" />
        <input v-model="accountForm.password" type="password" placeholder="Contraseña (mín. 8 caracteres)" minlength="8" required class="field" />
        <p v-if="accountError" class="text-sm text-rose-500">{{ accountError }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="accountLoading">
          {{ accountLoading ? "Creando cuenta..." : "Continuar" }}
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-muted">
        ¿Ya tienes cuenta? <NuxtLink to="/login?redirect=/registro/emprendimiento" class="font-semibold text-pink hover:underline">Inicia sesión</NuxtLink>
      </p>
    </div>

    <div v-else class="card mt-8 p-6">
      <p v-if="businessError" class="mb-4 text-sm text-rose-500">{{ businessError }}</p>
      <BusinessForm submit-label="Enviar para revisión" :loading="businessLoading" @submit="handleBusinessSubmit" />
    </div>
  </div>
</template>
