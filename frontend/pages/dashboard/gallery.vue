<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { BusinessImage } from "~/types";

definePageMeta({ layout: "dashboard", middleware: "auth" });

const businessStore = useBusinessStore();
await businessStore.fetchMyBusinesses();
const business = computed(() => businessStore.primaryBusiness);

const images = ref<BusinessImage[]>([]);
const loading = ref(false);
const confirmDeleteId = ref<number | null>(null);

async function loadImages() {
  if (!business.value) return;
  loading.value = true;
  try {
    const { data } = await businessService.listImages(business.value.id);
    images.value = Array.isArray(data) ? data : data.results;
  } finally {
    loading.value = false;
  }
}
await loadImages();

async function uploadFn(file: File) {
  if (!business.value) throw new Error("Primero crea tu emprendimiento");
  const { data } = await businessService.uploadImage(business.value.id, file);
  images.value = [...images.value, data];
  return data.image;
}

async function confirmDelete() {
  if (!confirmDeleteId.value || !business.value) return;
  await businessService.removeImage(business.value.id, confirmDeleteId.value);
  images.value = images.value.filter((img) => img.id !== confirmDeleteId.value);
  confirmDeleteId.value = null;
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Galería</h1>
    <p class="mt-1 text-sm text-muted">Muestra fotos de tu trabajo, tu espacio o tus productos.</p>

    <EmptyState v-if="!business" icon="briefcase" title="Primero crea tu emprendimiento" class="mt-8">
      <NuxtLink to="/dashboard/business" class="btn-primary mt-2">Crear emprendimiento</NuxtLink>
    </EmptyState>

    <template v-else>
      <div class="mt-6">
        <ImageUploader label="Agregar foto" :upload-fn="uploadFn" />
      </div>

      <LoadingSpinner v-if="loading" />
      <div v-else-if="images.length" class="mt-6 grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
        <div v-for="image in images" :key="image.id" class="group relative aspect-square overflow-hidden rounded-xl2 bg-gold-light">
          <img :src="image.image" class="h-full w-full object-cover" />
          <button
            class="absolute right-1.5 top-1.5 hidden h-7 w-7 items-center justify-center rounded-full bg-white text-rose-500 shadow-soft group-hover:flex"
            @click="confirmDeleteId = image.id"
          >
            <AppIcon name="trash" :size="14" />
          </button>
        </div>
      </div>
      <EmptyState v-else icon="images" title="Aún no subes fotos" description="Sube tu primera imagen para completar tu galería." class="mt-6" />
    </template>

    <ConfirmDialog
      :open="confirmDeleteId !== null"
      title="¿Eliminar imagen?"
      confirm-label="Eliminar"
      danger
      @confirm="confirmDelete"
      @cancel="confirmDeleteId = null"
    />
  </div>
</template>
