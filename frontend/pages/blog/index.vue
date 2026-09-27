<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import type {
  BlogPost,
  BlogCategory,
  BlogStage,
  BlogFormPayload,
} from "~/types";

const route = useRoute();
const router = useRouter();

const search = ref((route.query.search as string) || "");
const category = ref((route.query.category as string) || "");
const stage = ref((route.query.stage as string) || "");
const page = ref(Number(route.query.page) || 1);

// Categorías
const { data: categoriesData } = await useAsyncData(
  "blog-categories",
  async () => {
    const { data } = await blogService.categories({
      is_active: true,
    });

    return data;
  }
);

// Etapas
const { data: stagesData } = await useAsyncData(
  "blog-stages",
  async () => {
    const { data } = await blogService.stages({
      is_active: true,
    });

    return data;
  }
);

const categories = computed<BlogCategory[]>(() => {
  return categoriesData.value?.results || [];
});

const stages = computed<BlogStage[]>(() => {
  return stagesData.value?.results || [];
});

// Parámetros del listado
const params = computed(() => ({
  search: search.value || undefined,
  category: category.value || undefined,
  stage: stage.value || undefined,
  page: page.value,
}));

const { data, pending, refresh } = await useAsyncData(
  "blog-list",
  async () => {
    const { data } = await blogService.list(params.value);
    return data;
  },
  {
    watch: [params],
  }
);

// Actualizar URL
watch([search, category, stage, page], () => {
  router.replace({
    query: {
      ...(search.value ? { search: search.value } : {}),
      ...(category.value ? { category: category.value } : {}),
      ...(stage.value ? { stage: stage.value } : {}),
      page: String(page.value),
    },
  });
});

// Volver a página 1 cuando cambia un filtro
watch([search, category, stage], () => {
  page.value = 1;
});

// Si la URL cambia por fuera (ej. un link del menú a /blog?category=sueno
// mientras ya se está en /blog), sincroniza los filtros locales con ella.
watch(
  () => route.query,
  (query) => {
    search.value = (query.search as string) || "";
    category.value = (query.category as string) || "";
    stage.value = (query.stage as string) || "";
    page.value = Number(query.page) || 1;
  }
);

function openPost(slug: string) {
  navigateTo(`/blog/${slug}`);
}

const authStore = useAuthStore();
const featureFlagStore = useFeatureFlagStore();

// El blog puede tener activación programada (ver /admin/lanzamiento); el
// backend ya oculta el contenido para quien no sea admin, esto solo evita
// mostrar el "no encontramos artículos" genérico antes de la fecha.
const canSeeBlog = computed(() => featureFlagStore.isBlogLive || authStore.isAdmin);

const showCreate = ref(false);
const createLoading = ref(false);
const createError = ref("");
const createSuccess = ref(false);

function openCreate() {
  if (!authStore.isAuthenticated) {
    return navigateTo("/login?redirect=/blog");
  }

  createError.value = "";
  createSuccess.value = false;
  showCreate.value = true;
}

async function handleCreateSubmit(payload: BlogFormPayload) {
  createLoading.value = true;
  createError.value = "";

  try {
    await blogService.create(payload);

    createSuccess.value = true;

    await refresh();
  } catch (error) {
    createError.value = useErrorMessage(error);
  } finally {
    createLoading.value = false;
  }
}

function closeCreate() {
  showCreate.value = false;
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6">

    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
            <h1 class="text-2xl font-bold text-ink">Blog</h1>
            <p class="mt-1 text-sm text-muted">
                Contenido útil para acompañarte en cada etapa de la maternidad.
            </p>
        </div>
        <button
            v-if="canSeeBlog"
            type="button"
            class="btn-primary inline-flex items-center justify-center gap-2"
            @click="openCreate"
        >
        <AppIcon name="plus" :size="16" />
            Nuevo blog
        </button>
    </div>

    <!-- Filtros -->
    <div v-if="canSeeBlog" class="mt-6 flex flex-col gap-3 lg:flex-row lg:items-center">

      <!-- Buscar -->
      <div
        class="flex flex-1 items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5"
      >
        <AppIcon
          name="search"
          :size="16"
          class="text-muted"
        />

        <input
          v-model="search"
          type="text"
          placeholder="Buscar artículos..."
          class="w-full border-none bg-transparent text-sm outline-none"
        />
      </div>

      <!-- Categoría -->
      <select
        v-model="category"
        class="field lg:w-56"
      >
        <option value="">
          Todas las categorías
        </option>

        <option
          v-for="item in categories"
          :key="item.id"
          :value="item.slug"
        >
          {{ item.name }}
        </option>
      </select>

      <!-- Etapa -->
      <select
        v-model="stage"
        class="field lg:w-56"
      >
        <option value="">
          Todas las etapas
        </option>

        <option
          v-for="item in stages"
          :key="item.id"
          :value="item.slug"
        >
          {{ item.name }}
        </option>
      </select>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="pending" />

    <template v-else>

      <!-- Artículos -->
      <div
        v-if="data?.results?.length"
        class="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
      >

        <article
          v-for="post in data.results as BlogPost[]"
          :key="post.id"
          class="card group cursor-pointer overflow-hidden transition hover:-translate-y-1 hover:shadow-md"
          @click="openPost(post.slug)"
        >

          <!-- Imagen -->
          <div class="aspect-[4/3] overflow-hidden bg-gold-light">
            <img
              v-if="post.main_image"
              :src="post.main_image"
              :alt="post.title"
              class="h-full w-full object-cover transition duration-300 group-hover:scale-105"
            />

            <div
              v-else
              class="flex h-full w-full items-center justify-center text-gold"
            >
              <AppIcon
                name="file-text"
                :size="32"
              />
            </div>
          </div>

          <!-- Contenido -->
          <div class="p-4">

            <div class="flex flex-wrap items-center gap-2">
              <span class="badge bg-gold-light text-gold">
                {{ post.category_name }}
              </span>

              <span
                v-if="post.featured"
                class="badge bg-gold-light text-gold"
              >
                Destacado
              </span>
            </div>

            <h2
              class="mt-3 line-clamp-2 text-base font-semibold text-ink"
            >
              {{ post.title }}
            </h2>

            <p
              class="mt-2 line-clamp-3 text-sm text-muted"
            >
              {{ post.summary }}
            </p>

            <div
              class="mt-4 flex items-center justify-between text-xs text-muted"
            >
              <span>
                {{ post.reading_time }} min de lectura
              </span>

              <span class="text-gold">
                Leer más →
              </span>
            </div>

          </div>
        </article>

      </div>

      <!-- Vacío -->
      <EmptyState
        v-else-if="canSeeBlog"
        icon="search"
        title="No encontramos artículos"
        description="Prueba con otra búsqueda o cambia los filtros."
        class="mt-8"
      />

      <EmptyState
        v-else
        icon="clock"
        title="Muy pronto"
        description="El blog todavía no está disponible. Vuelve más adelante."
        class="mt-8"
      />

      <!-- Paginación -->
      <Pagination
        v-if="data && (data.next || data.previous)"
        :page="page"
        :has-next="Boolean(data.next)"
        :has-previous="Boolean(data.previous)"
        class="mt-8"
        @update:page="(p) => { page = p; refresh(); }"
      />

      <Teleport to="body">
        <div
            v-if="showCreate"
            class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4"
            @click.self="closeCreate"
        >
            <div
            class="card max-h-[90vh] w-full max-w-5xl overflow-y-auto p-6"
            >
            <template v-if="createSuccess">

                <div class="py-10 text-center">
                <AppIcon
                    name="check-circle"
                    :size="48"
                    class="mx-auto text-gold"
                />

                <h2 class="mt-4 text-xl font-semibold text-ink">
                    {{ authStore.isAdmin ? "¡Blog creado correctamente!" : "¡Gracias por tu aporte!" }}
                </h2>

                <p class="mt-2 text-sm text-muted">
                    {{
                      authStore.isAdmin
                        ? "El artículo fue guardado correctamente."
                        : "Tu artículo quedó en revisión. El equipo de Tribu Paridas lo publicará en cuanto lo apruebe."
                    }}
                </p>

                <button
                    type="button"
                    class="btn-primary mt-6"
                    @click="closeCreate"
                >
                    Listo
                </button>
                </div>

            </template>

            <template v-else>

                <div class="mb-6 flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-ink">
                    Nuevo blog
                    </h2>

                    <p class="mt-1 text-sm text-muted">
                    Crea un nuevo artículo para la comunidad.
                    </p>
                </div>

                <button
                    type="button"
                    class="text-muted hover:text-ink"
                    @click="closeCreate"
                >
                    <AppIcon
                    name="x"
                    :size="20"
                    />
                </button>
                </div>

                <div
                v-if="createError"
                class="mb-4 rounded-xl2 border border-red-200 bg-red-50 p-3 text-sm text-red-700"
                >
                {{ createError }}
                </div>

                <BlogForm
                submit-label="Crear blog"
                :loading="createLoading"
                @submit="handleCreateSubmit"
                />

            </template>
            </div>
        </div>
      </Teleport>

    </template>

  </div>
</template>