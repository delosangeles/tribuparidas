<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { Business } from "~/types";

const authStore = useAuthStore();

const form = reactive({ first_name: "", last_name: "", email: "", whatsapp: "", password: "" });
const loading = ref(false);
const error = ref("");
const submitted = ref(false);
const registerMessage = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";
  try {
    const data = await authStore.register({ ...form });
    registerMessage.value = data.detail;
    submitted.value = true;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

const featured = ref<Business[]>([]);

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
    <section class="relative overflow-hidden">
      <img :src="useAssetUrl('hero-inicio.png')" alt="Bienvenidas a nuestra página web" class="w-full" />
    </section>

    <section class="mx-auto max-w-7xl px-4 pt-8 sm:px-6">
      <CountdownTimer target="2026-09-01T19:00:00-05:00" label="¡Falta poco!" />
    </section>

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

  <div v-else class="mx-auto flex min-h-[80vh] max-w-md flex-col items-center justify-center px-4 py-16">
    <div class="text-center">
      <div class="flex justify-center">
        <BrandMark />
      </div>
      <h1 class="mt-4 text-2xl font-bold text-ink">Bienvenida a la tribu</h1>
      <p class="mt-1 text-sm text-muted">Regístrate e ingresa con tu usuario.</p>
    </div>

    <div v-if="submitted" class="card mt-8 w-full p-6 text-center">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500">
        <AppIcon name="check-circle" :size="26" />
      </span>
      <p class="mt-4 font-semibold text-ink">¡Registro recibido!</p>
      <p class="mt-1 text-sm text-muted">{{ registerMessage }}</p>
      <NuxtLink to="/login" class="btn-outline mt-4 inline-flex">Iniciar sesión</NuxtLink>
    </div>

    <div v-else class="card mt-8 w-full p-6">
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
            <input v-model="form.first_name" type="text" required class="field" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
            <input v-model="form.last_name" type="text" required class="field" />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Correo</label>
          <input v-model="form.email" type="email" required class="field" placeholder="tu@email.com" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">WhatsApp</label>
          <input
            v-model="form.whatsapp"
            type="text"
            required
            :pattern="PHONE_PATTERN"
            :title="PHONE_ERROR_MESSAGE"
            class="field"
            placeholder="+57 300 000 0000"
          />
          <p class="mt-1 text-xs text-muted">Con este número confirmamos que estás en el grupo de la tribu.</p>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña</label>
          <input v-model="form.password" type="password" required minlength="8" class="field" placeholder="Mínimo 8 caracteres" />
        </div>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary w-full" :disabled="loading">
          {{ loading ? "Enviando..." : "Registrarme" }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-muted">
        ¿Ya tienes cuenta?
        <NuxtLink to="/login" class="font-semibold text-gold hover:underline">Inicia sesión</NuxtLink>
      </p>
    </div>
  </div>
</template>
