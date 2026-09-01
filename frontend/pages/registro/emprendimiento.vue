<script setup lang="ts">
// Ruta protegida por el middleware global (requiere sesión aprobada).
const businessStore = useBusinessStore();

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
      <p class="mt-1 text-sm text-muted">Cuéntale a la tribu qué estás construyendo.</p>
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

    <div v-else class="card mt-8 p-6">
      <p v-if="businessError" class="mb-4 text-sm text-rose-500">{{ businessError }}</p>
      <BusinessForm submit-label="Enviar para revisión" :loading="businessLoading" @submit="handleBusinessSubmit" />
    </div>
  </div>
</template>
