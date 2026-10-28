<script setup lang="ts">
import { portalService } from "~/services/portal.service";

const authStore = useAuthStore();
const portal = usePortalStore();

// `owner`: las vendedoras solo ven el escáner, las estadísticas y el resumen.
const LINKS = [
  { to: "/portal", label: "Resumen", icon: "home", owner: false },
  { to: "/portal/escanear", label: "Escanear", icon: "camera", owner: false },
  { to: "/portal/emprendimiento", label: "Mi emprendimiento", icon: "briefcase", owner: true },
  { to: "/portal/imagenes", label: "Imágenes", icon: "images", owner: true },
  { to: "/portal/opiniones", label: "Opiniones", icon: "star", owner: true },
  { to: "/portal/preguntas", label: "Preguntas", icon: "message", owner: true },
  { to: "/portal/faq", label: "Preguntas frecuentes", icon: "file-text", owner: true },
  { to: "/portal/beneficio", label: "Beneficio Tribu", icon: "gift", owner: true },
  { to: "/portal/estadisticas", label: "Estadísticas", icon: "chart", owner: false },
  { to: "/portal/usuarias", label: "Usuarias", icon: "users", owner: true },
  { to: "/portal/historial", label: "Historial de cambios", icon: "clock", owner: true },
];

const links = computed(() => LINKS.filter((link) => !link.owner || portal.isOwner));
const menuOpen = ref(false);
const requestMessage = ref("");

async function requestConversion() {
  try {
    const { data } = await portalService.requestMemberConversion();
    requestMessage.value = data.detail;
  } catch (err) {
    requestMessage.value = useErrorMessage(err);
  }
}

async function handleLogout() {
  portal.reset();
  await authStore.logout();
  navigateTo("/");
}
</script>

<template>
  <aside class="flex w-full shrink-0 flex-col gap-1 border-line bg-white p-4 md:h-screen md:w-64 md:overflow-y-auto md:border-r">
    <div class="flex items-center justify-between">
      <NuxtLink to="/portal" class="flex items-center gap-2 px-3 text-sm font-semibold text-ink">
        <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="h-8 w-8" />
        Portal
      </NuxtLink>
      <button
        class="rounded-full border border-line p-2 text-ink md:hidden"
        aria-label="Abrir menú del portal"
        @click="menuOpen = !menuOpen"
      >
        <AppIcon :name="menuOpen ? 'x' : 'menu'" :size="18" />
      </button>
    </div>

    <div :class="[menuOpen ? 'flex' : 'hidden', 'flex-col gap-1 md:flex']">
      <label v-if="portal.businesses.length > 1" class="mt-3 px-1">
        <span class="px-2 text-xs font-semibold uppercase tracking-wide text-muted">Emprendimiento</span>
        <select
          class="field mt-1"
          :value="portal.currentId"
          @change="portal.select(Number(($event.target as HTMLSelectElement).value))"
        >
          <option v-for="b in portal.businesses" :key="b.business_id" :value="b.business_id">{{ b.name }}</option>
        </select>
      </label>
      <p v-else-if="portal.current" class="mt-3 px-3 text-sm font-medium text-ink">{{ portal.current.name }}</p>
      <p v-if="portal.current" class="px-3 pb-2 text-xs text-muted">
        {{ portal.current.role === "owner" ? "Dueña" : "Vendedora" }}
      </p>

      <NuxtLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="flex items-center gap-3 rounded-xl2 px-3 py-2.5 text-sm font-medium text-muted transition hover:bg-gold-light hover:text-gold"
        active-class="!bg-gold-light !text-gold"
        exact-active-class="!bg-gold-light !text-gold"
        @click="menuOpen = false"
      >
        <AppIcon :name="link.icon" :size="18" />
        {{ link.label }}
      </NuxtLink>

      <div class="mt-3 border-t border-line pt-3">
        <NuxtLink
          v-if="!authStore.isPortalAccount"
          to="/"
          class="flex items-center gap-3 rounded-xl2 px-3 py-2.5 text-sm font-medium text-muted hover:bg-gold-light hover:text-gold"
        >
          <AppIcon name="home" :size="18" /> Volver al sitio
        </NuxtLink>
        <template v-else>
          <button
            class="flex w-full items-center gap-3 rounded-xl2 px-3 py-2.5 text-left text-sm font-medium text-muted hover:bg-gold-light hover:text-gold"
            @click="requestConversion"
          >
            <AppIcon name="users" :size="18" /> Pedir cuenta de la página
          </button>
          <p v-if="requestMessage" class="px-3 pt-1 text-xs text-muted">{{ requestMessage }}</p>
        </template>
        <button
          class="mt-1 flex w-full items-center gap-3 rounded-xl2 px-3 py-2.5 text-left text-sm font-medium text-rose-500 hover:bg-rose-50"
          @click="handleLogout"
        >
          <AppIcon name="logout" :size="18" /> Cerrar sesión
        </button>
      </div>
    </div>
  </aside>
</template>
