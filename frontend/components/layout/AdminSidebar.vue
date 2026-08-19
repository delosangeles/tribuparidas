<script setup lang="ts">
const authStore = useAuthStore();

const links = [
  { to: "/admin", label: "Dashboard", icon: "chart" },
  { to: "/admin/businesses", label: "Emprendimientos", icon: "briefcase" },
  { to: "/admin/users", label: "Usuarios", icon: "users" },
  { to: "/admin/categories", label: "Categorías", icon: "box" },
];

async function handleLogout() {
  await authStore.logout();
  navigateTo("/");
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col gap-1 border-line bg-white p-4 md:h-full md:w-64 md:border-r">
    <p class="flex items-center gap-2 px-3 pb-4 text-sm font-bold text-ink">
      <span class="flex h-7 w-7 items-center justify-center rounded-full bg-ink text-white">
        <AppIcon name="logo" :size="14" />
      </span>
      Panel de administración
    </p>
    <NuxtLink
      v-for="link in links"
      :key="link.to"
      :to="link.to"
      class="flex items-center gap-3 rounded-xl2 px-3 py-2.5 text-sm font-medium text-muted transition hover:bg-gold-light hover:text-gold"
      active-class="!bg-gold-light !text-gold"
    >
      <AppIcon :name="link.icon" :size="18" />
      {{ link.label }}
    </NuxtLink>

    <button
      class="mt-4 flex items-center gap-3 rounded-xl2 px-3 py-2.5 text-left text-sm font-medium text-rose-500 hover:bg-rose-50"
      @click="handleLogout"
    >
      <AppIcon name="logout" :size="18" /> Cerrar sesión
    </button>
  </aside>
</template>
