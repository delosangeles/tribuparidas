<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import type {
  BlogCategory,
  BlogFormPayload,
  BlogPostDetail,
  BlogPostStatus,
  BlogStage,
  BlogContentType,
  BlogVisibility,
} from "~/types";

// Única categoría que se publica sin aprobación (ver OPEN_CATEGORY_SLUG en el backend).
const OPEN_CATEGORY_SLUG = "desahogos";

const props = withDefaults(
  defineProps<{
    submitLabel: string;
    loading?: boolean;
    initial?: BlogPostDetail | null;
    isAdmin?: boolean;
    authors?: { id: number; label: string }[];
  }>(),
  {
    loading: false,
    initial: null,
    isAdmin: false,
    authors: () => [],
  }
);

const emit = defineEmits<{
  (e: "submit", payload: BlogFormPayload): void;
}>();

// Categorías y etapas: este formulario se monta en varios contextos (modal
// público, crear y editar en el panel admin) — usar `getCachedData` fuerza
// una carga fresca en cada montaje en vez de reutilizar por siempre lo que
// haya quedado cacheado bajo esta misma key la primera vez que se abrió.
const { data: categoriesData } = await useAsyncData(
  "blog-form-categories",
  async () => {
    const { data } = await blogService.categories({
      is_active: true,
    });

    return data;
  },
  {
    getCachedData: () => undefined,
  }
);

const { data: stagesData } = await useAsyncData(
  "blog-form-stages",
  async () => {
    const { data } = await blogService.stages({
      is_active: true,
    });

    return data;
  },
  {
    getCachedData: () => undefined,
  }
);

const categories = computed<BlogCategory[]>(() => {
  const data = categoriesData.value;

  if (Array.isArray(data)) {
    return data;
  }

  return data?.results || [];
});

const stages = computed<BlogStage[]>(() => {
  const data = stagesData.value;

  if (Array.isArray(data)) {
    return data;
  }

  return data?.results || [];
});

const authorOptions = computed<{ id: number | string; label: string }[]>(() => [
  { id: "", label: "Sin cambios (por defecto, quien crea el post)" },
  ...props.authors,
]);

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

const STATUS_OPTIONS: { value: BlogPostStatus; label: string }[] = [
  {
    value: "DRAFT",
    label: "Borrador",
  },
  {
    value: "IN_REVIEW",
    label: "En revisi\u00f3n",
  },
  {
    value: "PUBLISHED",
    label: "Publicado",
  },
];

function formatDateTimeLocal(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60 * 1000);
  return localDate.toISOString().slice(0, 16);
}

const form = reactive({
  title: props.initial?.title || "",
  slug: props.initial?.slug || "",
  summary: props.initial?.summary || "",
  content: props.initial?.content || "",
  category: props.initial?.category ?? "",
  stages: props.initial?.stages_detail?.map((stage) => stage.id) || ([] as number[]),
  author: props.initial?.author ?? "",
  content_type: (props.initial?.content_type || "ARTICLE") as BlogContentType,
  publication_date: props.initial?.publication_date
    ? formatDateTimeLocal(props.initial.publication_date)
    : "",
  status: (props.initial?.status || "DRAFT") as BlogPostStatus,
  // Obligatorio: sin valor por defecto para que quien escribe elija.
  visibility: (props.initial?.visibility || "") as BlogVisibility | "",
  featured: props.initial?.featured ?? false,
  reading_time: props.initial?.reading_time ?? 5,
  sources: props.initial?.sources || "",
  seo_title: props.initial?.seo_title || "",
  seo_description: props.initial?.seo_description || "",
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
  // Al editar no se regenera el slug de un art\u00edculo que ya pudo haberse
  // compartido: cambiarlo romper\u00eda su URL.
  if (!props.initial) {
    form.slug = generateSlug(form.title);
  }
}

function handleSubmit() {
  if (!form.category || !form.content) {
    return;
  }

  const payload: BlogFormPayload = {
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
    visibility: form.visibility as BlogVisibility,
    featured: form.featured,
    reading_time: Number(form.reading_time),
    sources: form.sources,
    seo_title: form.seo_title,
    seo_description: form.seo_description,
  };

  if (props.isAdmin && form.author) {
    payload.author = Number(form.author);
  }

  emit("submit", payload);
}

const isOpenCategory = computed(
  () => categories.value.find((category) => category.id === Number(form.category))?.slug === OPEN_CATEGORY_SLUG
);
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
        :model-value="initial?.main_image"
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
            value=""
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

        <p v-if="!isAdmin && isOpenCategory" class="mt-1 text-xs text-gold-dark">
          💛 "Desahogos" se publica al instante, sin aprobación. Cuida el tono: es un espacio de respeto.
        </p>
        <p v-else-if="!isAdmin" class="mt-1 text-xs text-muted">
          Los artículos de esta categoría pasan por revisión del equipo antes de publicarse. Solo "Desahogos" se publica al instante.
        </p>
      </div>

      <!-- Visibilidad -->
      <div>
        <label class="mb-1 block text-sm font-medium text-ink">
          Visibilidad
        </label>

        <select v-model="form.visibility" required class="field">
          <option value="" disabled>Selecciona…</option>
          <option value="public">Público (lo ve cualquiera)</option>
          <option value="private">Privado (solo quienes tienen sesión)</option>
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

      <RichTextEditor
        v-model="form.content"
        placeholder="Escribe aquí el contenido completo del artículo..."
      />
    </div>

    <!-- Publicación -->
    <div class="rounded-xl2 border border-line p-4">
      <p class="mb-4 text-sm font-semibold text-ink">
        Publicación
      </p>

      <div v-if="isAdmin" class="mb-4 grid gap-4 sm:grid-cols-2">
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

        <!-- Autor -->
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">
            Autor
          </label>

          <SearchableSelect
            v-model="form.author"
            :options="authorOptions"
            placeholder="Buscar autor por nombre o correo..."
          />
        </div>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
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