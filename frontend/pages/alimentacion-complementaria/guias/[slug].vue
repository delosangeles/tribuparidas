<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";
import type { GuideDetail } from "~/types/alimentacion";

definePageMeta({ middleware: "alimentacion" });

const route = useRoute();
const authStore = useAuthStore();
const slug = route.params.slug as string;
const preview = route.query.preview === "1" && authStore.hasModule("alimentacion");

const guide = ref<GuideDetail | null>(null);
const loading = ref(true);
const notFound = ref(false);
const error = ref("");

try {
  guide.value = (await alimentacionService.guide(slug, preview)).data;
} catch (err: any) {
  if (err?.response?.status === 404) notFound.value = true;
  else error.value = useErrorMessage(err);
} finally {
  loading.value = false;
}

const g = guide.value;
usePageSeo({
  title: g ? g.title : "Guía no encontrada",
  description: g?.summary || "",
  path: `/alimentacion-complementaria/guias/${slug}`,
  image: g?.image,
});
if (!g) useHead({ meta: [{ name: "robots", content: "noindex" }] });
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
    <NuxtLink :to="{ path: '/alimentacion-complementaria', query: { seccion: 'guia' } }" class="inline-flex items-center gap-1 text-sm text-muted hover:text-gold">
      <AppIcon name="arrow" :size="14" class="rotate-180" /> Volver a la guía
    </NuxtLink>

    <MedicalDisclaimer />

    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="notFound" icon="file-text" title="No encontramos esta guía" />
    <p v-else-if="error" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">{{ error }}</p>

    <article v-else-if="guide" class="space-y-5">
      <p v-if="guide.status === 'draft'" class="rounded-xl2 bg-ink px-4 py-2 text-sm text-white">
        Vista previa: esta guía es un borrador y las usuarias todavía no la ven.
      </p>
      <img v-if="guide.image" :src="guide.image" :alt="guide.title" class="aspect-[16/9] w-full rounded-xl2 object-cover shadow-soft" />
      <h1 class="font-display text-3xl text-ink sm:text-4xl">{{ guide.title }}</h1>
      <p v-if="guide.summary" class="text-lg text-muted">{{ guide.summary }}</p>
      <div class="rich-content text-ink" v-html="guide.content" />
      <p class="text-xs text-muted">Última actualización: {{ new Date(guide.updated_at).toLocaleDateString("es-CO") }}</p>
    </article>
  </div>
</template>
