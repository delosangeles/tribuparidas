<script setup lang="ts">
const authStore = useAuthStore();
const featureFlagStore = useFeatureFlagStore();
const route = useRoute();
const menuOpen = ref(false);
const mobileNavOpen = ref(false);
const blogMenuOpen = ref(false);
const blogMenuRef = ref<HTMLElement | null>(null);

// Sub-items del menú "Blog": cada uno filtra el listado por una categoría o
// etapa ya existente (ver apps/blog/migrations/0002_seed_blog_data.py).
const BLOG_SUBMENU = [
  { label: "Sueño", to: "/blog?category=sueno" },
  { label: "Alimentación Complementaria", to: "/blog?category=alimentacion" },
  { label: "Embarazo", to: "/blog?stage=embarazo" },
];

// El blog puede tener activación programada (ver /admin/lanzamiento): se
// oculta del menú hasta esa fecha, salvo para el equipo admin que necesita
// entrar a prepararlo antes de que se revele.
const canSeeBlog = computed(() => featureFlagStore.isBlogLive || authStore.isAdmin);
// Igual que el blog: los festejos se revelan en la fecha de lanzamiento, pero
// el equipo admin los ve siempre para ir aprobándolos antes.
// Además son completamente privados: sin sesión no se muestran.
const canSeeFestejos = computed(
  () => authStore.isAuthenticated && (featureFlagStore.isFestejosLive || authStore.isAdmin)
);

// Cerrar al hacer click fuera. Antes usaba @mouseleave en el contenedor,
// pero el gap (mt-2) entre el botón y el desplegable hacía que el mouse
// "saliera" del contenedor al bajar y el menú se cerraba antes de poder
// hacer click en un sub-item.
function handleClickOutsideBlogMenu(event: MouseEvent) {
  if (blogMenuOpen.value && blogMenuRef.value && !blogMenuRef.value.contains(event.target as Node)) {
    blogMenuOpen.value = false;
  }
}

onMounted(() => document.addEventListener("click", handleClickOutsideBlogMenu));
onBeforeUnmount(() => document.removeEventListener("click", handleClickOutsideBlogMenu));

async function handleLogout() {
  await authStore.logout();
  menuOpen.value = false;
  mobileNavOpen.value = false;
  navigateTo("/");
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-line bg-white/90 backdrop-blur">
    <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
      <NuxtLink to="/">
        <BrandMark />
      </NuxtLink>

      <nav class="hidden items-center gap-6 text-sm font-medium text-muted md:flex">
        <NuxtLink to="/" class="transition hover:text-gold" active-class="text-gold">Inicio</NuxtLink>
        <NuxtLink to="/emprendimientos" class="transition hover:text-gold" active-class="text-gold">Emprendimientos</NuxtLink>
        <NuxtLink to="/noticias" class="transition hover:text-gold" active-class="text-gold">Noticias</NuxtLink>
        <NuxtLink v-if="canSeeFestejos" to="/festejos" class="transition hover:text-gold" active-class="text-gold">Festejos</NuxtLink>

        <div v-if="canSeeBlog" ref="blogMenuRef" class="relative">
          <button
            type="button"
            class="flex items-center gap-1 transition hover:text-gold"
            :class="route.path.startsWith('/blog') ? 'text-gold' : ''"
            @click="blogMenuOpen = !blogMenuOpen"
          >
            Blog
            <AppIcon name="chevron" :size="12" class="rotate-90" />
          </button>

          <div
            v-if="blogMenuOpen"
            class="absolute left-0 top-full z-10 mt-2 w-60 rounded-xl2 border border-line bg-white p-2 text-left shadow-soft"
            @click="blogMenuOpen = false"
          >
            <NuxtLink to="/blog" class="block rounded-xl2 px-3 py-2 text-ink transition hover:bg-gold-light hover:text-gold">
              Todos los blogs
            </NuxtLink>
            <div class="my-1 border-t border-line" />
            <p class="px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted">Por categoría</p>
            <NuxtLink
              v-for="item in BLOG_SUBMENU"
              :key="item.label"
              :to="item.to"
              class="block rounded-xl2 px-3 py-2 text-ink transition hover:bg-gold-light hover:text-gold"
            >
              {{ item.label }}
            </NuxtLink>
          </div>
        </div>
      </nav>

      <div class="flex items-center gap-2">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full border border-line text-ink md:hidden"
          @click="mobileNavOpen = !mobileNavOpen"
        >
          <AppIcon :name="mobileNavOpen ? 'x' : 'menu'" :size="18" />
        </button>

        <template v-if="!authStore.isAuthenticated">
          <NuxtLink to="/login" class="btn-outline">Iniciar sesión</NuxtLink>
        </template>

        <div v-else class="relative">
          <button
            class="flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm font-medium text-ink hover:border-gold"
            @click="menuOpen = !menuOpen"
          >
            <UserAvatar
              :src="authStore.user?.photo"
              :name="authStore.user?.first_name || authStore.user?.email"
              size="sm"
            />
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

    <nav
      v-if="mobileNavOpen"
      class="flex flex-col gap-1 border-t border-line px-4 py-3 text-sm font-medium text-muted md:hidden"
    >
      <NuxtLink
        to="/"
        class="rounded-xl2 px-3 py-2.5 transition hover:bg-gold-light hover:text-gold"
        active-class="!bg-gold-light !text-gold"
        @click="mobileNavOpen = false"
      >
        Inicio
      </NuxtLink>
      <NuxtLink
        to="/emprendimientos"
        class="rounded-xl2 px-3 py-2.5 transition hover:bg-gold-light hover:text-gold"
        active-class="!bg-gold-light !text-gold"
        @click="mobileNavOpen = false"
      >
        Emprendimientos
      </NuxtLink>
      <NuxtLink
        to="/noticias"
        class="rounded-xl2 px-3 py-2.5 transition hover:bg-gold-light hover:text-gold"
        active-class="!bg-gold-light !text-gold"
        @click="mobileNavOpen = false"
      >
        Noticias
      </NuxtLink>
      <NuxtLink
        v-if="canSeeFestejos"
        to="/festejos"
        class="rounded-xl2 px-3 py-2.5 transition hover:bg-gold-light hover:text-gold"
        active-class="!bg-gold-light !text-gold"
        @click="mobileNavOpen = false"
      >
        Festejos
      </NuxtLink>
      <template v-if="canSeeBlog">
        <NuxtLink
          to="/blog"
          class="rounded-xl2 px-3 py-2.5 transition hover:bg-gold-light hover:text-gold"
          active-class="!bg-gold-light !text-gold"
          @click="mobileNavOpen = false"
        >
          Blog
        </NuxtLink>
        <p class="mt-1 px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-muted/60">Blog por categoría</p>
        <NuxtLink
          v-for="item in BLOG_SUBMENU"
          :key="item.label"
          :to="item.to"
          class="rounded-xl2 py-2.5 pl-6 pr-3 transition hover:bg-gold-light hover:text-gold"
          @click="mobileNavOpen = false"
        >
          {{ item.label }}
        </NuxtLink>
      </template>
    </nav>
  </header>
</template>
