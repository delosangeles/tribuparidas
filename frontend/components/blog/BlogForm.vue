<script setup lang="ts">
import type {
  BlogCategory,
  BlogFormPayload,
  BlogStage,
  BlogContentType,
} from "~/types";

const props = withDefaults(
  defineProps<{
    submitLabel: string;
    loading?: boolean;
  }>(),
  {
    loading: false,
  }
);

const emit = defineEmits<{
  (e: "submit", payload: BlogFormPayload): void;
}>();

// Categorías
const { data: categoriesData } = await useAsyncData(
  "blog-form-categories",
  async () => {
    const { data } = await blogService.categories({
      is_active: true,
    });

    return data;
  }
);

// Etapas
const { data: stagesData } = await useAsyncData(
  "blog-form-stages",
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

const CONTENT_TYPES: {
  value: BlogContentType;
  label: string;
}[] = [
  {
    value: "ARTICLE",
    label: "Artículo",
  },
  {
    value: "GUIDE",
    label: "Guía",
  },
  {
    value: "CHECKLIST",
    label: "Checklist",
  },
  {
    value: "RESOURCE",
    label: "Recurso",
  },
  {
    value: "RECOMMENDATION",
    label: "Recomendación",
  },
  {
    value: "TRIBU_STORY",
    label: "Historia de la tribu",
  },
];

const STATUS_OPTIONS = [
  {
    value: "DRAFT",
    label: "Borrador",
  },
  {
    value: "PUBLISHED",
    label: "Publicado",
  },
];

const form = reactive({
  title: "",
  slug: "",
  summary: "",
  content: "",
  category: 0,
  stages: [] as number[],
  content_type: "ARTICLE" as BlogContentType,
  publication_date: "",
  status: "DRAFT",
  featured: false,
  reading_time: 5,
  sources: "",
  seo_title: "",
  seo_description: "",
});

const mainImage = ref<File | null>(null);

function generateSlug(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function handleTitleInput() {
  form.slug = generateSlug(form.title);
}

function handleSubmit() {
  emit("submit", {
    title: form.title,
    slug: form.slug,
    summary: form.summary,
    content: form.content,
    main_image: mainImage.value,
    category: Number(form.category),
    stages: form.stages.map(Number),
    content_type: form.content_type,
    publication_date: form.publication_date || null,
    status: form.status,
    featured: form.featured,
    reading_time: Number(form.reading_time),
    sources: form.sources,
    seo_title: form.seo_title,
    seo_description: form.seo_description,
  });
}
</script>

<template>
  <form
    class="space-y-6"
    @submit.prevent="handleSubmit"
  >
    <!-- Imagen -->
    <div>
      <p class="mb-2 text-sm font-medium text-ink">
        Imagen principal
      </p>

      <ImageUploader
        shape="wide"
        label="Subir imagen"
        @select="(file) => (mainImage = file)"
      />
    </div>

    <!-- Información principal -->
    <div class="grid gap-4 sm:grid-cols-2">
      <!-- Título -->
      <div class="sm:col-span-2">
        <label class="mb-1 block text-sm font-medium text-ink">
          Título
        </label>

        <input
          v-model="form.title"
          type="text"
          required
          class="field"
          placeholder="Ej: Guía para preparar la llegada del bebé"
          @input="handleTitleInput"
        />
      </div>

      <!-- Slug -->
      <div class="sm:col-span-2">
        <label class="mb-1 block text-sm font-medium text-ink">
          Slug
        </label>

        <input
          v-model="form.slug"
          type="text"
          required
          class="field"
          placeholder="guia-para-preparar-la-llegada-del-bebe"
        />

        <p class="mt-1 text-xs text-muted">
          Será utilizado en la URL del artículo.
        </p>
      </div>

      <!-- Categoría -->
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Categoría
        </label>

        <select
          v-model="form.category"
          required
          class="field"
        >
          <option
            :value="0"
            disabled
          >
            Selecciona una categoría
          </option>

          <option
            v-for="category in categories"
            :key="category.id"
            :value="category.id"
          >
            {{ category.name }}
          </option>
        </select>
      </div>

      <!-- Tipo -->
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Tipo de contenido
        </label>

        <select
          v-model="form.content_type"
          required
          class="field"
        >
          <option
            v-for="type in CONTENT_TYPES"
            :key="type.value"
            :value="type.value"
          >
            {{ type.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Etapas -->
    <div>
      <label class="mb-2 block text-sm font-medium text-ink">
        Etapas de maternidad
      </label>

      <div
        v-if="stages.length"
        class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3"
      >
        <label
          v-for="stage in stages"
          :key="stage.id"
          class="flex cursor-pointer items-center gap-2 rounded-xl2 border border-line px-3 py-2.5 text-sm transition hover:border-gold"
          :class="
            form.stages.includes(stage.id)
              ? 'border-gold bg-gold-light/40'
              : 'bg-white'
          "
        >
          <input
            v-model="form.stages"
            type="checkbox"
            :value="stage.id"
            class="accent-gold"
          />

          <span class="text-ink">
            {{ stage.name }}
          </span>
        </label>
      </div>

      <p
        v-else
        class="text-sm text-muted"
      >
        No hay etapas activas disponibles.
      </p>
    </div>

    <!-- Resumen -->
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">
        Resumen
      </label>

      <textarea
        v-model="form.summary"
        rows="3"
        required
        class="field"
        placeholder="Una breve descripción que aparecerá en las tarjetas del blog..."
      />
    </div>

    <!-- Contenido -->
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">
        Contenido
      </label>

      <textarea
        v-model="form.content"
        rows="12"
        required
        class="field"
        placeholder="Escribe aquí el contenido completo del artículo..."
      />
    </div>

    <!-- Publicación -->
    <div class="rounded-xl2 border border-line p-4">
      <p class="mb-4 text-sm font-semibold text-ink">
        Publicación
      </p>

      <div class="grid gap-4 sm:grid-cols-3">
        <!-- Estado -->
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Estado
          </label>

          <select
            v-model="form.status"
            class="field"
          >
            <option
              v-for="option in STATUS_OPTIONS"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <!-- Fecha -->
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Fecha de publicación
          </label>

          <input
            v-model="form.publication_date"
            type="datetime-local"
            class="field"
          />
        </div>

        <!-- Lectura -->
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Tiempo de lectura
          </label>

          <div class="flex items-center gap-2">
            <input
              v-model.number="form.reading_time"
              type="number"
              min="1"
              required
              class="field"
            />

            <span class="text-sm text-muted">
              min
            </span>
          </div>
        </div>
      </div>

      <!-- Destacado -->
      <label class="mt-4 flex cursor-pointer items-center gap-2 text-sm">
        <input
          v-model="form.featured"
          type="checkbox"
          class="accent-gold"
        />

        <span class="font-medium text-ink">
          Mostrar como artículo destacado
        </span>
      </label>
    </div>

    <!-- Fuentes -->
    <div>
      <label class="mb-1 block text-sm font-medium text-ink">
        Fuentes
      </label>

      <textarea
        v-model="form.sources"
        rows="3"
        class="field"
        placeholder="Fuentes, referencias o enlaces utilizados..."
      />
    </div>

    <!-- SEO -->
    <div class="rounded-xl2 border border-line p-4">
      <p class="mb-4 text-sm font-semibold text-ink">
        SEO
      </p>

      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            SEO title
          </label>

          <input
            v-model="form.seo_title"
            type="text"
            class="field"
            placeholder="Título optimizado para buscadores"
          />
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            SEO description
          </label>

          <textarea
            v-model="form.seo_description"
            rows="3"
            class="field"
            placeholder="Descripción que podrán mostrar los buscadores..."
          />
        </div>
      </div>
    </div>

    <!-- Submit -->
    <button
      type="submit"
      class="btn-primary"
      :disabled="loading"
    >
      {{ loading ? "Guardando..." : submitLabel }}
    </button>
  </form>
</template>