<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import { userService } from "~/services/user.service";
import type { AdminModule } from "~/types";

const authStore = useAuthStore();

// `module`: las madrinas solo ven los enlaces de los módulos que tienen asignados.
const BASE_LINKS: { to: string; label: string; icon: string; module?: AdminModule }[] = [
  { to: "/admin", label: "Dashboard", icon: "chart" },
  { to: "/admin/businesses", label: "Emprendimientos", icon: "briefcase" },
  { to: "/admin/blog", label: "Blog", icon: "file-text", module: "blog" },
  { to: "/admin/news", label: "Noticias", icon: "newspaper" },
  { to: "/admin/users", label: "Usuarios", icon: "users", module: "usuarios" },
  { to: "/admin/duenas", label: "Portal de emprendimientos", icon: "briefcase" },
  { to: "/admin/membresias", label: "Membresías", icon: "shield" },
  { to: "/admin/festejos", label: "Festejos", icon: "gift", module: "festejos" },
  { to: "/admin/alimentacion", label: "Alimentación complementaria", icon: "leaf", module: "alimentacion" },
  { to: "/admin/categories", label: "Categorías", icon: "box" },
  { to: "/admin/activity", label: "Historial", icon: "clock" },
  { to: "/admin/ajustes", label: "Ajustes", icon: "settings" },
];

const SUPERADMIN_LINKS = [
  { to: "/admin/analytics", label: "Analítica", icon: "chart" },
  { to: "/admin/madrinas", label: "Madrinas", icon: "shield" },
  { to: "/admin/reportes", label: "Reportes mensuales", icon: "file-text" },
  { to: "/admin/launch", label: "Lanzamiento", icon: "star" },
];

const links = computed(() => {
  if (authStore.isSuperAdmin) return [...BASE_LINKS, ...SUPERADMIN_LINKS];
  if (authStore.isAdmin) return BASE_LINKS;
  return BASE_LINKS.filter((link) => link.module && authStore.hasModule(link.module));
});

// Contadores del menú; una madrina solo pide los de sus módulos.
const pendingUsers = ref(0);
if (authStore.hasModule("usuarios")) {
  userService
    .adminList({ needs_review: true, page_size: 1 })
    .then(({ data }) => {
      pendingUsers.value = data.count;
    })
    .catch(() => {});
}

const pendingBlogPosts = ref(0);
if (authStore.hasModule("blog")) {
  blogService
    .list({ status: "IN_REVIEW", page_size: 1 })
    .then(({ data }) => {
      pendingBlogPosts.value = data.count;
    })
    .catch(() => {});
}

// En celular el menú va plegado para no empujar el contenido fuera de la primera pantalla.
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
        :aria-label="menuOpen ? 'Cerrar menú del panel' : 'Abrir menú del panel'"
        :aria-expanded="menuOpen"
        @click="menuOpen = !menuOpen"
      >
        <AppIcon :name="menuOpen ? 'x' : 'menu'" :size="18" />
      </button>
    </div>
    <div :class="[menuOpen ? 'flex' : 'hidden', 'flex-col gap-1 md:flex']">
    <p class="px-3 pb-3 pt-3 text-xs font-semibold uppercase tracking-wide text-muted md:pt-0">Panel de administración</p>
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
      <span v-if="link.to === '/admin/blog' && pendingBlogPosts > 0" class="rounded-full bg-gold px-2 py-0.5 text-xs font-semibold text-white">
        {{ pendingBlogPosts }}
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
