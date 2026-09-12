<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { Business } from "~/types";

const authStore = useAuthStore();

// const form = reactive({ first_name: "", last_name: "", email: "", whatsapp: "", password: "" });
// const loading = ref(false);
// const error = ref("");
// const submitted = ref(false);
// const registerMessage = ref("");

// async function handleSubmit() {
//   loading.value = true;
//   error.value = "";
//   try {
//     const data = await authStore.register({ ...form });
//     registerMessage.value = data.detail;
//     submitted.value = true;
//   } catch (err) {
//     error.value = useErrorMessage(err);
//   } finally {
//     loading.value = false;
//   }
// }

const featured = ref<Business[]>([]);

if (!authStore.isAuthenticated) {
  await navigateTo("/login");
}

if (authStore.isAuthenticated) {
  const { data } = await businessService.list({ ordering: "name", page_size: 8 });
  featured.value = data.results;
}

const searchQuery = ref("");
function submitSearch() {
  navigateTo({ path: "/emprendimientos", query: searchQuery.value ? { search: searchQuery.value } : {} });
}
</script>

<template>
  <div v-if="authStore.isAuthenticated">
    <section class="w-full flex justify-center overflow-hidden">
      <NuxtLink
        to="https://wa.me/+573008478168?text=Hola%20Maria%20Isabel%20de%20Tribu%20Paridas,%20quiero%20inscribirme%20en%20la%20Media%20Marat%C3%B3n%20de%20Palmira"
        class="block w-full md:w-3/4 max-w-[1400px]"
      >
        <picture>
          <source
            media="(max-width: 767px)"
            :srcset="useAssetUrl('MaratonMamas2709.jpg')"
          />

          <img
            :src="useAssetUrl('MaratonMamas2709BAnner.jpg')"
            alt="Mamás en movimiento - Media Maratón Internacional Ciudad de Palmira"
            class="w-full h-auto block"
          />
        </picture>
      </NuxtLink>
    </section>
    <!-- <img :src="useAssetUrl('hero-inicio.png')" alt="Bienvenidas a nuestra página web" class="w-full" /> -->

    <!-- <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6">
      <CountdownTimer target="2026-09-01T19:00:00-05:00" label="¡Falta poco!" />
    </section> -->

    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6">
      <form class="mx-auto flex max-w-lg items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 shadow-soft" @submit.prevent="submitSearch">
        <AppIcon name="search" :size="16" class="text-muted" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar emprendimiento, categoría o ciudad..."
          class="w-full border-none bg-transparent text-sm outline-none"
        />
        <button type="submit" class="btn-primary shrink-0">Buscar</button>
      </form>
    </section>

    <section class="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="flex items-center gap-2 text-xl font-bold text-ink">
          <AppIcon name="heart" :size="18" class="text-gold" />
          Emprendimientos destacados
        </h2>
        <NuxtLink to="/emprendimientos" class="text-sm font-semibold text-gold hover:underline">Ver todos</NuxtLink>
      </div>

      <div v-if="featured?.length" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <BusinessCard v-for="business in featured" :key="business.id" :business="business" />
      </div>
      <EmptyState v-else icon="briefcase" title="Todavía no hay emprendimientos publicados" description="Vuelve pronto, estamos sumando nuevas historias." />
    </section>
  </div>
</template>
