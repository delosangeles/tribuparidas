<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { Business, BusinessFormPayload } from "~/types";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const businessStore = useBusinessStore();
const categoriesStore = useCategoriesStore();
await categoriesStore.fetchAll();

const showCreate = ref(false);
const createLoading = ref(false);
const createError = ref("");
const createSuccess = ref(false);

function openCreate() {
  if (!authStore.isAuthenticated) return navigateTo({ path: "/login", query: { redirect: "/emprendimientos" } });
  createError.value = "";
  createSuccess.value = false;
  showCreate.value = true;
}

async function handleCreateSubmit(payload: BusinessFormPayload) {
  createLoading.value = true;
  createError.value = "";
  try {
    await businessStore.createBusiness(payload);
    createSuccess.value = true;
  } catch (err) {
    createError.value = useErrorMessage(err);
  } finally {
    createLoading.value = false;
  }
}

function closeCreate() {
  showCreate.value = false;
}

const search = ref((route.query.search as string) || "");
const category = ref((route.query.category as string) || "");
const ordering = ref((route.query.ordering as string) || "-created_at");
const page = ref(Number(route.query.page) || 1);

const params = computed(() => ({
  search: search.value || undefined,
  category__slug: category.value || undefined,
  ordering: ordering.value,
  page: page.value,
}));

const { data, pending, refresh } = await useAsyncData(
  "businesses-list",
  async () => {
    const { data } = await businessService.list(params.value);
    return data;
  },
  { watch: [params] }
);

watch([search, category, ordering, page], () => {
  router.replace({
    query: {
      ...(search.value ? { search: search.value } : {}),
      ...(category.value ? { category: category.value } : {}),
      ordering: ordering.value,
      page: String(page.value),
    },
  });
});

watch([search, category, ordering], () => {
  page.value = 1;
});
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
    <h1 class="text-2xl font-bold text-ink">Emprendimientos</h1>
    <p class="mt-1 text-sm text-muted">Explora todos los emprendimientos aprobados en la comunidad.</p>

    <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="flex flex-1 items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5">
        <AppIcon name="search" :size="16" class="text-muted" />
        <input v-model="search" type="text" placeholder="Buscar por nombre, descripción o ciudad..." class="w-full border-none bg-transparent text-sm outline-none" />
      </div>
      <button class="btn-primary shrink-0" @click="openCreate">
        <AppIcon name="briefcase" :size="16" /> Crear emprendimiento
      </button>
      <select v-model="category" class="field sm:w-56">
        <option value="">Todas las categorías</option>
        <option v-for="c in categoriesStore.items" :key="c.id" :value="c.slug">{{ c.name }}</option>
      </select>
      <select v-model="ordering" class="field sm:w-56">
        <option value="-created_at">Más recientes</option>
        <option value="-average_rating">Mejor calificados</option>
        <option value="name">Nombre A-Z</option>
      </select>
    </div>

    <LoadingSpinner v-if="pending" />
    <template v-else>
      <div v-if="data?.results?.length" class="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <BusinessCard v-for="business in data.results as Business[]" :key="business.id" :business="business" />
      </div>
      <EmptyState
        v-else
        icon="search"
        title="No encontramos emprendimientos"
        description="Prueba con otra búsqueda o cambia los filtros."
        class="mt-8"
      />

      <Pagination
        v-if="data && (data.next || data.previous)"
        :page="page"
        :has-next="Boolean(data.next)"
        :has-previous="Boolean(data.previous)"
        class="mt-8"
        @update:page="(p) => { page = p; refresh(); }"
      />
    </template>

    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-ink/40 px-4 py-8">
        <div class="card max-h-[90vh] w-full max-w-5xl overflow-y-auto p-6">
          <template v-if="createSuccess">
            <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500">
              <AppIcon name="check-circle" :size="26" />
            </span>
            <p class="mt-4 text-center font-semibold text-ink">¡Tu emprendimiento fue enviado!</p>
            <p class="mt-1 text-center text-sm text-muted">
              Queda pendiente hasta que el equipo admin lo revise y lo apruebe.
            </p>
            <button class="btn-primary mt-6 w-full" @click="closeCreate">Listo</button>
          </template>
          <template v-else>
            <div class="flex items-center justify-between">
              <p class="text-lg font-semibold text-ink">Crear emprendimiento</p>
              <button class="btn-ghost !px-2 !py-1" @click="closeCreate">
                <AppIcon name="x" :size="18" />
              </button>
            </div>
            <p v-if="createError" class="mt-2 text-sm text-rose-500">{{ createError }}</p>
            <div class="mt-4">
              <BusinessForm submit-label="Crear emprendimiento" :loading="createLoading" require-all @submit="handleCreateSubmit" />
            </div>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>
