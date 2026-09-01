<script setup lang="ts">
const authStore = useAuthStore();
const menuOpen = ref(false);

const COMING_SOON_LINKS = ["Sueño", "Alimentación Complementaria", "Embarazo", "Blogs"];

async function handleLogout() {
  await authStore.logout();
  menuOpen.value = false;
  navigateTo("/");
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-line bg-white/90 backdrop-blur">
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
      <NuxtLink to="/">
        <BrandMark />
      </NuxtLink>

      <nav v-if="authStore.isAuthenticated" class="hidden items-center gap-6 text-sm font-medium text-muted md:flex">
        <NuxtLink to="/" class="transition hover:text-gold" active-class="text-gold">Inicio</NuxtLink>
        <NuxtLink to="/emprendimientos" class="transition hover:text-gold" active-class="text-gold">Emprendimientos</NuxtLink>
        <span v-for="label in COMING_SOON_LINKS" :key="label" class="flex cursor-default flex-col items-center gap-1 text-center text-muted/60">
          {{ label }}
          <span class="rounded-full bg-rose-500 px-1.5 py-0.5 text-[9px] font-semibold uppercase leading-none text-white">¡Próximamente!</span>
        </span>
      </nav>

      <div class="flex items-center gap-2">
        <template v-if="!authStore.isAuthenticated">
          <NuxtLink to="/login" class="btn-outline">Iniciar sesión</NuxtLink>
        </template>

        <div v-else class="relative">
          <button
            class="flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm font-medium text-ink hover:border-gold"
            @click="menuOpen = !menuOpen"
          >
            <span class="flex h-7 w-7 items-center justify-center rounded-full bg-gold-light text-xs font-semibold text-gold">
              {{ authStore.user?.first_name?.charAt(0) || authStore.user?.email.charAt(0) }}
            </span>
            {{ authStore.user?.first_name || "Mi cuenta" }}
          </button>

          <div
            v-if="menuOpen"
            class="absolute right-0 mt-2 w-52 rounded-xl2 border border-line bg-white p-2 shadow-soft"
            @click="menuOpen = false"
          >
            <NuxtLink v-if="authStore.isAdmin" to="/admin" class="flex items-center gap-2 rounded-xl2 px-3 py-2 text-sm text-ink hover:bg-gold-light">
              <AppIcon name="settings" :size="16" /> Panel admin
            </NuxtLink>
            <NuxtLink to="/dashboard/settings" class="flex items-center gap-2 rounded-xl2 px-3 py-2 text-sm text-ink hover:bg-gold-light">
              <AppIcon name="users" :size="16" /> Mi perfil
            </NuxtLink>
            <button class="flex w-full items-center gap-2 rounded-xl2 px-3 py-2 text-left text-sm text-rose-500 hover:bg-rose-50" @click="handleLogout">
              <AppIcon name="logout" :size="16" /> Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
