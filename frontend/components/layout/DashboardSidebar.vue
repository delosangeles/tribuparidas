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

const menuOpen = ref(false);
watch(() => useRoute().fullPath, () => {
  menuOpen.value = false;
});

async function handleLogout() {
  await authStore.logout();
  navigateTo("/");
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col gap-1 border-b border-line bg-white p-4 max-md:sticky max-md:top-0 max-md:z-40 max-md:max-h-screen max-md:overflow-y-auto md:h-full md:w-64 md:border-b-0 md:border-r">
    <div class="flex items-center justify-between md:block">
      <NuxtLink to="/" class="flex items-center gap-2 px-3 text-sm font-medium text-muted transition hover:text-gold md:mb-3">
        <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="h-8 w-8" />
        Volver al inicio
      </NuxtLink>
      <button
        type="button"
        class="rounded-full border border-line p-2 text-ink md:hidden"
        :aria-label="menuOpen ? 'Cerrar menú' : 'Abrir menú'"
        :aria-expanded="menuOpen"
        @click="menuOpen = !menuOpen"
      >
        <AppIcon :name="menuOpen ? 'x' : 'menu'" :size="18" />
      </button>
    </div>
    <div :class="[menuOpen ? 'flex' : 'hidden', 'flex-col gap-1 md:flex']">
    <p class="px-3 pb-3 pt-3 text-xs font-semibold uppercase tracking-wide text-muted md:pt-0">
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
    </div>
  </aside>
</template>
