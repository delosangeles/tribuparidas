<script setup lang="ts">
import { newsService } from "~/services/news.service";
import type { News } from "~/types";

const news = ref<News[]>([]);
const loading = ref(true);

const page = ref(1);
const pagination = ref<{
  next: string | null;
  previous: string | null;
}>({
  next: null,
  previous: null,
});

async function loadNews() {
  loading.value = true;

  try {
    const { data } = await newsService.list({
      page: page.value,
      page_size: 12,
      ordering: "-published_at",
    });

    news.value = data.results;

    pagination.value = {
      next: data.next,
      previous: data.previous,
    };
  } catch (error) {
    console.error("Error cargando noticias:", error);
    news.value = [];
  } finally {
    loading.value = false;
  }
}

function changePage(nextPage: number) {
  page.value = nextPage;
  loadNews();
}

function getNewsStatus(item: News) {
  const now = new Date();
  const publishedAt = new Date(item.published_at);
  const expiresAt = new Date(item.expires_at);

  if (!item.is_active) {
    return {
      label: "Inactiva",
      class: "bg-gray-100 text-gray-500",
    };
  }

  if (now < publishedAt) {
    return {
      label: "Próximamente",
      class: "bg-amber-50 text-amber-600",
    };
  }

  if (now > expiresAt) {
    return {
      label: "Finalizada",
      class: "bg-gray-100 text-gray-500",
    };
  }

  return {
    label: "Activa",
    class: "bg-emerald-50 text-emerald-600",
  };
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

await loadNews();
</script>

<template>
  <div class="min-h-screen bg-vanilla">
    <!-- Encabezado -->
    <section class="mx-auto max-w-7xl px-4 pb-8 pt-10 sm:px-6">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-ink sm:text-4xl">
          Noticias
        </h1>

        <p class="mx-auto mt-2 max-w-2xl text-sm text-muted sm:text-base">
          Conoce las novedades, actividades, beneficios y noticias de nuestra
          Tribu Paridas.
        </p>
      </div>
    </section>

    <!-- Loading -->
    <section
      v-if="loading"
      class="mx-auto max-w-7xl px-4 py-8 sm:px-6"
    >
      <LoadingSpinner />
    </section>

    <!-- Noticias -->
    <section
      v-else-if="news.length"
      class="mx-auto max-w-7xl px-4 pb-12 sm:px-6"
    >
      <!-- 4 por fila en escritorio -->
      <div
        class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        <article
          v-for="item in news"
          :key="item.id"
          class="flex flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md"
        >
          <!-- Imagen -->
          <a
            v-if="item.link"
            :href="item.link"
            target="_blank"
            rel="noopener noreferrer"
            class="block"
          >
            <picture>
              <source
                media="(max-width: 767px)"
                :srcset="item.image_mobile"
              />

              <img
                :src="item.image_desktop"
                :alt="item.title"
                class="aspect-[16/9] w-full object-cover"
              />
            </picture>
          </a>

          <picture v-else>
            <source
              media="(max-width: 767px)"
              :srcset="item.image_mobile"
            />

            <img
              :src="item.image_desktop"
              :alt="item.title"
              class="aspect-[16/9] w-full object-cover"
            />
          </picture>

          <!-- Contenido -->
          <div class="flex flex-1 flex-col p-4">
            <!-- Estado -->
            <div class="mb-3 flex items-center justify-between gap-2">
              <span
                class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                :class="getNewsStatus(item).class"
              >
                {{ getNewsStatus(item).label }}
              </span>

              <span class="text-xs text-muted">
                {{ formatDate(item.published_at) }}
              </span>
            </div>

            <!-- Título -->
            <h2 class="text-lg font-bold leading-tight text-ink">
              {{ item.title }}
            </h2>

            <!-- Descripción -->
            <p
              v-if="item.description"
              class="mt-3 flex-1 whitespace-pre-line text-sm leading-6 text-muted"
            >
              {{ item.description }}
            </p>

            <!-- Fecha de vencimiento -->
            <div
              class="mt-4 border-t border-line pt-3 text-xs text-muted"
            >
              Disponible hasta:
              <span class="font-medium text-ink">
                {{ formatDate(item.expires_at) }}
              </span>
            </div>

            <!-- Botón -->
            <a
              v-if="item.link"
              :href="item.link"
              target="_blank"
              rel="noopener noreferrer"
              class="btn-primary mt-4 w-full justify-center"
            >
              Ver información
            </a>
          </div>
        </article>
      </div>

      <!-- Paginación -->
      <Pagination
        v-if="pagination.next || pagination.previous"
        :page="page"
        :has-next="Boolean(pagination.next)"
        :has-previous="Boolean(pagination.previous)"
        class="mt-8"
        @update:page="changePage"
      />
    </section>

    <!-- Sin noticias -->
    <section
      v-else
      class="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6"
    >
      <h2 class="text-xl font-semibold text-ink">
        No hay noticias disponibles
      </h2>

      <p class="mt-2 text-sm text-muted">
        En este momento no tenemos noticias para mostrar.
      </p>
    </section>
  </div>
</template>