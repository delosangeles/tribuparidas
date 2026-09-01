<script setup lang="ts">
const authStore = useAuthStore();
const questionsStore = useQuestionsStore();

const ENTREPRENEUR_LINKS = [
  { to: "/dashboard", label: "Inicio", icon: "home" },
  { to: "/dashboard/business", label: "Mi emprendimiento", icon: "briefcase" },
  { to: "/dashboard/gallery", label: "Galería", icon: "images" },
  { to: "/dashboard/questions", label: "Preguntas", icon: "message" },
  { to: "/dashboard/stats", label: "Estadísticas", icon: "chart" },
];
const SETTINGS_LINK = { to: "/dashboard/settings", label: "Configuración", icon: "settings" };

const links = computed(() =>
  authStore.isEntrepreneur ? [...ENTREPRENEUR_LINKS, SETTINGS_LINK] : [SETTINGS_LINK]
);

async function handleLogout() {
  await authStore.logout();
  navigateTo("/");
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col gap-1 border-line bg-white p-4 md:h-full md:w-64 md:border-r">
    <p class="px-3 pb-3 text-xs font-semibold uppercase tracking-wide text-muted">
      {{ authStore.isEntrepreneur ? "Emprendedor" : "Mi cuenta" }}
    </p>
    <NuxtLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="flex items-center justify-between rounded-xl2 px-3 py-2.5 text-sm font-medium text-muted transition hover:bg-gold-light hover:text-gold"
      active-class="!bg-gold-light !text-gold"
    >
      <span class="flex items-center gap-3">
        <AppIcon :name="link.icon" :size="18" />
        {{ link.label }}
      </span>
      <span
        v-if="link.to === '/dashboard/questions' && questionsStore.pendingCount > 0"
        class="rounded-full bg-gold px-2 py-0.5 text-xs font-semibold text-white"
      >
        {{ questionsStore.pendingCount }}
      </span>
    </NuxtLink>

    <button
      class="mt-4 flex items-center gap-3 rounded-xl2 px-3 py-2.5 text-left text-sm font-medium text-rose-500 hover:bg-rose-50"
      @click="handleLogout"
    >
      <AppIcon name="logout" :size="18" /> Cerrar sesión
    </button>
  </aside>
</template>
