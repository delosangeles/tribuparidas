<script setup lang="ts">
import type { News, NewsFormPayload } from "~/types";

const props = withDefaults(
  defineProps<{
    initial?: News | null;
    submitLabel: string;
    loading?: boolean;
  }>(),
  {
    initial: null,
    loading: false,
  }
);

const emit = defineEmits<{
  (e: "submit", payload: NewsFormPayload): void;
}>();

const form = reactive({
  title: props.initial?.title || "",
  description: props.initial?.description || "",
  link: props.initial?.link || "",
  published_at: props.initial?.published_at
    ? formatDateTimeLocal(props.initial.published_at)
    : "",
  expires_at: props.initial?.expires_at
    ? formatDateTimeLocal(props.initial.expires_at)
    : "",
  order: props.initial?.order ?? 0,
  is_active: props.initial?.is_active ?? true,
});

const desktopFile = ref<File | null>(null);
const mobileFile = ref<File | null>(null);

const desktopError = ref("");
const mobileError = ref("");

function formatDateTimeLocal(value: string) {
  const date = new Date(value);

  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60 * 1000);

  return localDate.toISOString().slice(0, 16);
}

function handleSubmit() {
  desktopError.value = "";
  mobileError.value = "";

  if (!props.initial?.image_desktop && !desktopFile.value) {
    desktopError.value = "La imagen para PC es obligatoria.";
    return;
  }

  if (!props.initial?.image_mobile && !mobileFile.value) {
    mobileError.value = "La imagen para móvil es obligatoria.";
    return;
  }

  if (
    form.expires_at &&
    form.published_at &&
    new Date(form.expires_at) <= new Date(form.published_at)
  ) {
    alert("La fecha de vencimiento debe ser posterior a la fecha de publicación.");
    return;
  }

  emit("submit", {
    title: form.title,
    description: form.description,
    link: form.link,
    published_at: form.published_at,
    expires_at: form.expires_at,
    order: Number(form.order),
    is_active: form.is_active,
    image_desktop: desktopFile.value,
    image_mobile: mobileFile.value,
  });
}
</script>

<template>
  <form class="space-y-5" @submit.prevent="handleSubmit">

    <!-- Información -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

      <div class="sm:col-span-2 lg:col-span-3">
        <label class="mb-1 block text-sm font-medium text-ink">
          Título
        </label>

        <input
          v-model="form.title"
          type="text"
          required
          maxlength="200"
          class="field"
          placeholder="Ej: Nueva emprendedora de la Tribu"
        />
      </div>

      <div class="sm:col-span-2 lg:col-span-3">
        <label class="mb-1 block text-sm font-medium text-ink">
          Descripción
        </label>

        <textarea
          v-model="form.description"
          rows="4"
          class="field"
          placeholder="Escribe una descripción para la noticia..."
        />
      </div>

      <div class="sm:col-span-2">
        <label class="mb-1 block text-sm font-medium text-ink">
          Enlace
        </label>

        <input
          v-model="form.link"
          type="url"
          class="field"
          placeholder="https://tribuparidas.com/..."
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Orden
        </label>

        <input
          v-model.number="form.order"
          type="number"
          min="0"
          class="field"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Fecha de publicación
        </label>

        <input
          v-model="form.published_at"
          type="datetime-local"
          required
          class="field"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Fecha de vencimiento
        </label>

        <input
          v-model="form.expires_at"
          type="datetime-local"
          required
          class="field"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Estado
        </label>

        <select v-model="form.is_active" class="field">
          <option :value="true">Activa</option>
          <option :value="false">Inactiva</option>
        </select>
      </div>

    </div>

    <!-- Imágenes -->
    <div class="rounded-xl2 border border-line p-4">
      <p class="mb-4 text-sm font-semibold text-ink">
        Imágenes del banner
      </p>

      <div class="grid gap-6 lg:grid-cols-2">

        <!-- PC -->
        <div>
          <p class="mb-2 text-sm font-medium text-ink">
            Imagen para PC
          </p>

          <ImageUploader
            :model-value="initial?.image_desktop"
            label="Banner PC"
            @select="(file) => (desktopFile = file)"
          />

          <p class="mt-1 text-xs text-muted">
            Recomendado: formato horizontal para escritorio.
          </p>

          <p
            v-if="desktopError"
            class="mt-1 text-xs text-rose-500"
          >
            {{ desktopError }}
          </p>
        </div>

        <!-- Móvil -->
        <div>
          <p class="mb-2 text-sm font-medium text-ink">
            Imagen para móvil
          </p>

          <ImageUploader
            :model-value="initial?.image_mobile"
            label="Banner móvil"
            @select="(file) => (mobileFile = file)"
          />

          <p class="mt-1 text-xs text-muted">
            Recomendado: formato vertical para dispositivos móviles.
          </p>

          <p
            v-if="mobileError"
            class="mt-1 text-xs text-rose-500"
          >
            {{ mobileError }}
          </p>
        </div>

      </div>
    </div>

    <!-- Botón -->
    <button
      type="submit"
      class="btn-primary"
      :disabled="loading"
    >
      {{ loading ? "Guardando..." : submitLabel }}
    </button>

  </form>
</template>