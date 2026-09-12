<script setup lang="ts">
import { newsService } from "~/services/news.service";
import type { News, NewsFormPayload } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const search = ref("");
const activeFilter = ref<"all" | "active" | "inactive">("all");
const page = ref(1);

const loading = ref(false);
const news = ref<News[]>([]);
const pagination = ref<{
  next: string | null;
  previous: string | null;
}>({
  next: null,
  previous: null,
});

const actingId = ref<number | null>(null);

const showForm = ref(false);
const editing = ref<News | null>(null);
const formLoading = ref(false);
const formError = ref("");

async function load() {
  loading.value = true;

  try {
    const params: Record<string, unknown> = {
      page: page.value,
      ordering: "-created_at",
    };

    if (search.value) {
      params.search = search.value;
    }

    if (activeFilter.value === "active") {
      params.is_active = true;
    }

    if (activeFilter.value === "inactive") {
      params.is_active = false;
    }

    const { data } = await newsService.list(params);

    news.value = data.results;

    pagination.value = {
      next: data.next,
      previous: data.previous,
    };
  } finally {
    loading.value = false;
  }
}

await load();

watch([search, activeFilter], () => {
  page.value = 1;
  load();
});

function changePage(next: number) {
  page.value = next;
  load();
}

function openCreate() {
  editing.value = null;
  formError.value = "";
  showForm.value = true;
}

function openEdit(item: News) {
  editing.value = item;
  formError.value = "";
  showForm.value = true;
}

async function toggleActive(item: News) {
  actingId.value = item.id;

  try {
    await newsService.update(item.id, {
      is_active: !item.is_active,
    });

    item.is_active = !item.is_active;
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    actingId.value = null;
  }
}

async function remove(item: News) {
  const confirmed = window.confirm(
    `¿Estás segura de que deseas eliminar la noticia "${item.title}"?`
  );

  if (!confirmed) return;

  actingId.value = item.id;

  try {
    await newsService.remove(item.id);
    news.value = news.value.filter((newsItem) => newsItem.id !== item.id);
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    actingId.value = null;
  }
}

async function handleSubmit(payload: NewsFormPayload) {
  formLoading.value = true;
  formError.value = "";

  try {
    if (editing.value) {
      await newsService.update(editing.value.id, payload);
    } else {
      await newsService.create(payload);
    }

    showForm.value = false;
    await load();
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    formLoading.value = false;
  }
}
</script>

<template>
  <div>
    <!-- Encabezado -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink">Noticias</h1>

        <p class="mt-1 text-sm text-muted">
          Administra los banners y noticias que aparecen en la página principal.
        </p>
      </div>

      <button class="btn-primary" @click="openCreate">
        <AppIcon name="plus" :size="16" />
        Nueva noticia
      </button>
    </div>

    <!-- Formulario -->
    <div v-if="showForm" class="card mt-6 p-6">
      <p class="mb-4 font-semibold text-ink">
        {{ editing ? "Editar noticia" : "Nueva noticia" }}
      </p>

      <p v-if="formError" class="mb-4 text-sm text-rose-500">
        {{ formError }}
      </p>

      <NewsForm
        :initial="editing"
        :submit-label="editing ? 'Guardar cambios' : 'Crear noticia'"
        :loading="formLoading"
        @submit="handleSubmit"
      />

      <button
        type="button"
        class="btn-ghost mt-2"
        @click="showForm = false"
      >
        Cancelar
      </button>
    </div>

    <!-- Búsqueda -->
    <div
      class="mt-6 flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 sm:max-w-sm"
    >
      <AppIcon name="search" :size="16" class="text-muted" />

      <input
        v-model="search"
        type="text"
        placeholder="Buscar noticia..."
        class="w-full border-none bg-transparent text-sm outline-none"
      />
    </div>

    <!-- Filtros -->
    <div class="mt-3 flex flex-wrap gap-2">
      <button
        class="btn-outline"
        :class="activeFilter === 'all' && '!border-gold !text-gold'"
        @click="activeFilter = 'all'"
      >
        Todas
      </button>

      <button
        class="btn-outline"
        :class="activeFilter === 'active' && '!border-gold !text-gold'"
        @click="activeFilter = 'active'"
      >
        Activas
      </button>

      <button
        class="btn-outline"
        :class="activeFilter === 'inactive' && '!border-gold !text-gold'"
        @click="activeFilter = 'inactive'"
      >
        Inactivas
      </button>
    </div>

    <!-- Tabla -->
    <LoadingSpinner v-if="loading" />

    <div
      v-else
      class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white"
    >
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Noticia</th>
            <th class="px-4 py-3">Publicación</th>
            <th class="px-4 py-3">Vencimiento</th>
            <th class="px-4 py-3">Creado por</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-line">
          <tr v-for="item in news" :key="item.id">
            <!-- Noticia -->
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="item.image_desktop"
                  :src="item.image_desktop"
                  :alt="item.title"
                  class="h-12 w-20 rounded-lg object-cover"
                />

                <div>
                  <p class="font-medium text-ink">
                    {{ item.title }}
                  </p>

                  <p
                    v-if="item.description"
                    class="mt-1 max-w-xs truncate text-xs text-muted"
                  >
                    {{ item.description }}
                  </p>
                </div>
              </div>
            </td>

            <!-- Publicación -->
            <td class="px-4 py-3 text-muted">
              {{ new Date(item.published_at).toLocaleString("es-CO") }}
            </td>

            <!-- Vencimiento -->
            <td class="px-4 py-3 text-muted">
              {{ new Date(item.expires_at).toLocaleString("es-CO") }}
            </td>

            <!-- Creado por -->
            <td class="px-4 py-3 text-muted">
              {{ item.created_by_name }}
            </td>

            <!-- Estado -->
            <td class="px-4 py-3">
              <span
                v-if="item.is_active"
                class="inline-flex rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-600"
              >
                Activa
              </span>

              <span
                v-else
                class="inline-flex rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-500"
              >
                Inactiva
              </span>
            </td>

            <!-- Acciones -->
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <a
                  v-if="item.link"
                  :href="item.link"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="btn-ghost !px-2 !py-1"
                >
                  Ver
                </a>

                <button
                  class="btn-outline !px-2 !py-1 text-xs"
                  @click="openEdit(item)"
                >
                  Editar
                </button>

                <button
                  class="btn-outline !px-2 !py-1 text-xs"
                  :class="
                    item.is_active
                      ? '!text-amber-600'
                      : '!text-emerald-600'
                  "
                  :disabled="actingId === item.id"
                  @click="toggleActive(item)"
                >
                  {{ item.is_active ? "Desactivar" : "Activar" }}
                </button>

                <button
                  class="btn-outline !px-2 !py-1 text-xs !text-rose-500"
                  :disabled="actingId === item.id"
                  @click="remove(item)"
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p
        v-if="!news.length"
        class="py-8 text-center text-sm text-muted"
      >
        No hay noticias con este filtro.
      </p>
    </div>

    <!-- Paginación -->
    <Pagination
      v-if="pagination.next || pagination.previous"
      :page="page"
      :has-next="Boolean(pagination.next)"
      :has-previous="Boolean(pagination.previous)"
      class="mt-4"
      @update:page="changePage"
    />
  </div>
</template>
