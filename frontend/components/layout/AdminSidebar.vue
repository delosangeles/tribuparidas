<script setup lang="ts">
import { userService } from "~/services/user.service";

const authStore = useAuthStore();

const links = [
  { to: "/admin", label: "Dashboard", icon: "chart" },
  { to: "/admin/businesses", label: "Emprendimientos", icon: "briefcase" },
  { to: "/admin/users", label: "Usuarios", icon: "users" },
  { to: "/admin/categories", label: "Categorías", icon: "box" },
  { to: "/admin/activity", label: "Historial", icon: "clock" },
];

const pendingUsers = ref(0);
userService.adminList({ is_active: false, page_size: 1 }).then(({ data }) => {
  pendingUsers.value = data.count;
});

async function handleLogout() {
  await authStore.logout();
  navigateTo("/");
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col gap-1 border-line bg-white p-4 md:h-full md:w-64 md:border-r">
    <NuxtLink to="/" class="mb-3 flex items-center gap-2 px-3 text-sm font-medium text-muted transition hover:text-gold">
      <img src="/logo-mark.png" alt="Tribu Paridas" class="h-8 w-8" />
      Volver al inicio
    </NuxtLink>
    <p class="px-3 pb-3 text-xs font-semibold uppercase tracking-wide text-muted">Panel de administración</p>
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
      <span v-if="link.to === '/admin/users' && pendingUsers > 0" class="rounded-full bg-gold px-2 py-0.5 text-xs font-semibold text-white">
        {{ pendingUsers }}
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
