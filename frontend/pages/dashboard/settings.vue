<script setup lang="ts">
definePageMeta({ layout: "dashboard", middleware: "auth" });

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
</script>

<template>
  <div class="max-w-lg">
    <h1 class="text-2xl font-bold text-ink">Configuración</h1>
    <p class="mt-1 text-sm text-muted">Actualiza tus datos personales.</p>

    <div class="card mt-6 p-6">
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
        <p v-if="success" class="text-sm text-emerald-600">Perfil actualizado.</p>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary" :disabled="loading">Guardar cambios</button>
      </form>
    </div>
  </div>
</template>
