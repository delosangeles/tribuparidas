<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalImage } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const MAX_IMAGES = 4;
const images = ref<PortalImage[]>([]);
const busy = ref(false);
const error = ref("");
const toDelete = ref<PortalImage | null>(null);
const input = ref<HTMLInputElement | null>(null);

const { businessId } = usePortalBusiness(load);

async function load() {
  images.value = (await portalService.images(businessId.value)).data;
}

async function onPick(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files ?? []);
  (event.target as HTMLInputElement).value = "";
  error.value = "";
  busy.value = true;
  try {
    for (const file of files) {
      if (images.value.length >= MAX_IMAGES) {
        error.value = `Máximo ${MAX_IMAGES} imágenes.`;
        break;
      }
      const compressed = await compressImage(file); // valida tipo/tamaño y reduce antes de subir
      const { data } = await portalService.uploadImage(businessId.value, compressed);
      images.value.push(data);
    }
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    busy.value = false;
  }
}

async function reorder(ids: number[]) {
  busy.value = true;
  try {
    images.value = (await portalService.reorderImages(businessId.value, ids)).data;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    busy.value = false;
  }
}

function move(index: number, delta: number) {
  const ids = images.value.map((i) => i.id);
  const target = index + delta;
  if (target < 0 || target >= ids.length) return;
  [ids[index], ids[target]] = [ids[target], ids[index]];
  reorder(ids);
}

function makeMain(index: number) {
  const ids = images.value.map((i) => i.id);
  const [picked] = ids.splice(index, 1);
  reorder([picked, ...ids]);
}

async function remove() {
  if (!toDelete.value) return;
  try {
    await portalService.deleteImage(businessId.value, toDelete.value.id);
    await load();
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    toDelete.value = null;
  }
}
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-5">
    <header class="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold text-ink">Imágenes</h1>
        <p class="text-sm text-muted">Hasta {{ MAX_IMAGES }} fotos (JPG, PNG o WEBP). La principal es la primera.</p>
      </div>
      <div>
        <input ref="input" type="file" accept="image/jpeg,image/png,image/webp" multiple class="hidden" @change="onPick" />
        <button class="btn-primary" :disabled="busy || images.length >= MAX_IMAGES" @click="input?.click()">
          <AppIcon name="plus" :size="16" /> {{ busy ? "Procesando..." : "Subir imágenes" }}
        </button>
      </div>
    </header>

    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
    <EmptyState v-if="!images.length" icon="images" title="Aún no tienes imágenes" description="Sube fotos de tus productos o servicios." />

    <ul class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <li v-for="(image, index) in images" :key="image.id" class="card overflow-hidden">
        <div class="relative">
          <img :src="image.image" alt="" class="aspect-square w-full object-cover" />
          <span v-if="image.is_main" class="badge absolute left-2 top-2 bg-gold text-white">Principal</span>
        </div>
        <div class="flex flex-wrap items-center gap-1 p-2">
          <button class="btn-ghost !px-2 !py-1" :disabled="busy || index === 0" aria-label="Mover antes" @click="move(index, -1)"><AppIcon name="arrow" :size="14" class="-rotate-90" /></button>
          <button class="btn-ghost !px-2 !py-1" :disabled="busy || index === images.length - 1" aria-label="Mover después" @click="move(index, 1)"><AppIcon name="arrow" :size="14" class="rotate-90" /></button>
          <button v-if="!image.is_main" class="btn-ghost !px-2 !py-1 text-xs" :disabled="busy" @click="makeMain(index)">Hacer principal</button>
          <button class="btn-ghost ml-auto !px-2 !py-1 !text-rose-500" aria-label="Eliminar" @click="toDelete = image"><AppIcon name="trash" :size="14" /></button>
        </div>
      </li>
    </ul>

    <ConfirmDialog
      :open="Boolean(toDelete)"
      title="¿Eliminar esta imagen?"
      description="Esta acción no se puede deshacer."
      confirm-label="Eliminar"
      danger
      @confirm="remove"
      @cancel="toDelete = null"
    />
  </div>
</template>
