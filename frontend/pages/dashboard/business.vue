<script setup lang="ts">
definePageMeta({ layout: "dashboard", middleware: "auth" });

const businessStore = useBusinessStore();
await businessStore.fetchMyBusinesses();

const business = computed(() => businessStore.primaryBusiness);
const loading = ref(false);
const error = ref("");
const success = ref(false);

async function handleSubmit(payload: any) {
  loading.value = true;
  error.value = "";
  success.value = false;
  try {
    if (business.value) {
      await businessStore.updateBusiness(business.value.id, payload);
    } else {
      await businessStore.createBusiness(payload);
    }
    success.value = true;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Mi emprendimiento</h1>
    <p class="mt-1 text-sm text-muted">
      {{ business ? "Actualiza la información pública de tu emprendimiento." : "Completa los datos para publicar tu emprendimiento." }}
    </p>

    <div v-if="business" class="mt-4">
      <StatusBadge :status="business.status" />
    </div>

    <div class="card mt-6 p-6">
      <p v-if="success" class="mb-4 rounded-xl2 bg-emerald-50 p-3 text-sm text-emerald-600">
        Cambios guardados correctamente.
      </p>
      <p v-if="error" class="mb-4 text-sm text-rose-500">{{ error }}</p>
      <BusinessForm
        :initial="business"
        :submit-label="business ? 'Guardar cambios' : 'Crear emprendimiento'"
        :loading="loading"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>
