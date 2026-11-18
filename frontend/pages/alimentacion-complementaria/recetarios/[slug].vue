<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { CookbookDetail } from "~/types/alimentacion";

definePageMeta({ middleware: "alimentacion" });

const route = useRoute();
const authStore = useAuthStore();
const slug = route.params.slug as string;
const preview = route.query.preview === "1" && authStore.hasModule("alimentacion");

const book = ref<CookbookDetail | null>(null);
const loading = ref(true);
const notFound = ref(false);
const error = ref("");

try {
  book.value = (await alimentacionService.cookbook(slug, preview)).data;
} catch (err: any) {
  if (err?.response?.status === 404) notFound.value = true;
  else error.value = useErrorMessage(err);
} finally {
  loading.value = false;
}

const b = book.value;
usePageSeo({
  title: b ? b.title : "Recetario no encontrado",
  description: b?.summary || "",
  path: `/alimentacion-complementaria/recetarios/${slug}`,
  image: b?.image,
});
if (!b) useHead({ meta: [{ name: "robots", content: "noindex" }] });
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
    <NuxtLink :to="{ path: '/alimentacion-complementaria', query: { seccion: 'recetarios' } }" class="inline-flex items-center gap-1 text-sm text-muted hover:text-gold">
      <AppIcon name="arrow" :size="14" class="rotate-180" /> Volver a los recetarios
    </NuxtLink>

    <MedicalDisclaimer />

    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="notFound" icon="file-text" title="No encontramos este recetario" />
    <p v-else-if="error" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">{{ error }}</p>

    <article v-else-if="book" class="space-y-5">
      <p v-if="book.status === 'draft'" class="rounded-xl2 bg-ink px-4 py-2 text-sm text-white">
        Vista previa: este recetario es un borrador y las usuarias todavía no lo ven.
      </p>
      <header class="space-y-2">
        <h1 class="font-display text-3xl text-ink sm:text-4xl">{{ book.title }}</h1>
        <span v-if="book.age_range" class="badge bg-gold-light text-gold-dark">{{ book.age_range.name }}</span>
        <p v-if="book.summary" class="text-lg text-muted">{{ book.summary }}</p>
      </header>

      <template v-if="book.pdf">
        <div class="flex flex-wrap gap-2">
          <a :href="book.pdf" target="_blank" rel="noopener" class="btn-primary">Abrir en pantalla completa</a>
          <a :href="book.pdf" download class="btn-outline">Descargar PDF</a>
        </div>
        <!-- En celulares algunos navegadores no incrustan PDF: por eso los botones de arriba. -->
        <iframe
          :src="book.pdf"
          :title="book.title"
          class="h-[75vh] w-full rounded-xl2 border border-line bg-white shadow-soft"
        />
      </template>
      <EmptyState v-else icon="file-text" title="Este recetario aún no tiene archivo" />
    </article>
  </div>
</template>
