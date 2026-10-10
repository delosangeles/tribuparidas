<script setup lang="ts">
// Aviso (no bloquea el acceso) para usuarias que aún no completan sus datos
// de festejos: cumpleaños, o nombre/fecha de algún hijo.
const authStore = useAuthStore();
const featureFlagStore = useFeatureFlagStore();
const route = useRoute();

const missing = computed(() => authStore.user?.missing_festejos_data || []);
const show = computed(
  () =>
    authStore.isAuthenticated &&
    featureFlagStore.isFestejosLive &&
    missing.value.length > 0 &&
    !authStore.isAdmin &&
    route.path !== "/dashboard/settings"
);
</script>

<template>
  <div v-if="show" class="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
    <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2">
      <p>
        <strong>Completa tus datos para los festejos:</strong>
        te falta {{ missing.join(", ") }}.
      </p>
      <NuxtLink to="/dashboard/settings" class="font-semibold underline">Completar ahora</NuxtLink>
    </div>
  </div>
</template>
