<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import { userService } from "~/services/user.service";
import type { BlogPost, BlogPostDetail, BlogFormPayload, User } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin", module: "blog" });

const authStore = useAuthStore();

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  IN_REVIEW: "En revisión",
  PUBLISHED: "Publicado",
};

const STATUS_BADGE_CLASS: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-500",
  IN_REVIEW: "bg-amber-50 text-amber-600",
  PUBLISHED: "bg-emerald-50 text-emerald-600",
};

const search = ref("");
const statusFilter = ref<"all" | "DRAFT" | "IN_REVIEW" | "PUBLISHED">("all");
const page = ref(1);

const loading = ref(false);
const posts = ref<BlogPost[]>([]);
const pagination = ref<{ next: string | null; previous: string | null }>({
  next: null,
  previous: null,
});

const users = ref<User[]>([]);

const actingSlug = ref<string | null>(null);

const showForm = ref(false);
const editing = ref<BlogPostDetail | null>(null);
const formLoading = ref(false);
const formError = ref("");

function userLabel(user: { first_name: string; last_name: string; email: string }) {
  const name = `${user.first_name} ${user.last_name}`.trim();
  return name ? `${name} (${user.email})` : user.email;
}

const authorOptions = computed(() => {
  const options = users.value.map((user) => ({ id: user.id, label: userLabel(user) }));

  if (editing.value && !options.some((option) => option.id === editing.value?.author)) {
    options.unshift({ id: editing.value.author, label: editing.value.author_name });
  }

  return options;
});

async function loadUsers() {
  // Solo las administradoras (o madrinas con acceso a Usuarios) pueden listar autoras.
  if (!authStore.hasModule("usuarios")) return;
  try {
    const { data } = await userService.adminList({ page_size: 100 });
    users.value = data.results;
  } catch {
    users.value = [];
  }
}

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

    if (statusFilter.value !== "all") {
      params.status = statusFilter.value;
    }

    const { data } = await blogService.list(params);

    posts.value = data.results;
    pagination.value = { next: data.next, previous: data.previous };
  } finally {
    loading.value = false;
  }
}

await Promise.all([load(), loadUsers()]);

watch([search, statusFilter], () => {
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

async function openEdit(item: BlogPost) {
  formError.value = "";

  const { data } = await blogService.retrieve(item.slug);
  editing.value = data;
  showForm.value = true;
}

function closeForm() {
  showForm.value = false;
  editing.value = null;
}

async function handleSubmit(payload: BlogFormPayload) {
  formLoading.value = true;
  formError.value = "";

  try {
    if (editing.value) {
      await blogService.update(editing.value.slug, payload);
    } else {
      await blogService.create(payload);
    }

    closeForm();
    await load();
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    formLoading.value = false;
  }
}

async function approve(item: BlogPost) {
  actingSlug.value = item.slug;

  try {
    await blogService.approve(item.slug);
    await load();
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    actingSlug.value = null;
  }
}

async function reject(item: BlogPost) {
  const confirmed = window.confirm(`¿Rechazar "${item.title}"? Vuelve a borrador, no se publica ni se borra.`);

  if (!confirmed) return;

  actingSlug.value = item.slug;

  try {
    await blogService.reject(item.slug);
    await load();
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    actingSlug.value = null;
  }
}

async function remove(item: BlogPost) {
  const confirmed = window.confirm(`¿Eliminar el blog "${item.title}"? Esta acción no se puede deshacer.`);

  if (!confirmed) return;

  actingSlug.value = item.slug;

  try {
    await blogService.remove(item.slug);
    posts.value = posts.value.filter((post) => post.slug !== item.slug);
  } catch (err) {
    formError.value = useErrorMessage(err);
  } finally {
    actingSlug.value = null;
  }
}
</script>

<template>
  <div>
    <!-- Encabezado -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-ink">Blog</h1>

        <p class="mt-1 text-sm text-muted">
          Administra los artículos del blog y aprueba los que envían las usuarias.
        </p>
      </div>

      <button v-if="authStore.can('blog', 'add')" class="btn-primary" @click="openCreate">
        <AppIcon name="plus" :size="16" />
        Nuevo blog
      </button>
    </div>

    <!-- Formulario -->
    <div v-if="showForm" class="card mt-6 p-6">
      <p class="mb-4 font-semibold text-ink">
        {{ editing ? "Editar blog" : "Nuevo blog" }}
      </p>

      <p v-if="formError" class="mb-4 text-sm text-rose-500">
        {{ formError }}
      </p>

      <BlogForm
        :initial="editing"
        :submit-label="editing ? 'Guardar cambios' : 'Crear blog'"
        :loading="formLoading"
        :is-admin="authStore.isAdmin"
        :authors="authorOptions"
        @submit="handleSubmit"
      />

      <button type="button" class="btn-ghost mt-2" @click="closeForm">
        Cancelar
      </button>
    </div>

    <!-- Búsqueda -->
    <div class="mt-6 flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 sm:max-w-sm">
      <AppIcon name="search" :size="16" class="text-muted" />

      <input
        v-model="search"
        type="text"
        placeholder="Buscar blog..."
        class="w-full border-none bg-transparent text-sm outline-none"
      />
    </div>

    <!-- Filtros -->
    <div class="mt-3 flex flex-wrap gap-2">
      <button
        class="btn-outline"
        :class="statusFilter === 'all' && '!border-gold !text-gold'"
        @click="statusFilter = 'all'"
      >
        Todos
      </button>

      <button
        class="btn-outline"
        :class="statusFilter === 'IN_REVIEW' && '!border-gold !text-gold'"
        @click="statusFilter = 'IN_REVIEW'"
      >
        En revisión
      </button>

      <button
        class="btn-outline"
        :class="statusFilter === 'PUBLISHED' && '!border-gold !text-gold'"
        @click="statusFilter = 'PUBLISHED'"
      >
        Publicados
      </button>

      <button
        class="btn-outline"
        :class="statusFilter === 'DRAFT' && '!border-gold !text-gold'"
        @click="statusFilter = 'DRAFT'"
      >
        Borradores
      </button>
    </div>

    <!-- Tabla -->
    <LoadingSpinner v-if="loading" />

    <div v-else class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Blog</th>
            <th class="px-4 py-3">Categoría</th>
            <th class="px-4 py-3">Autor</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Comentarios</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-line">
          <tr v-for="item in posts" :key="item.id">
            <!-- Blog -->
            <td class="px-4 py-3">
              <div class="flex items-center gap-3">
                <img
                  v-if="item.main_image"
                  :src="item.main_image"
                  :alt="item.title"
                  class="h-12 w-16 rounded-lg object-cover"
                />

                <p class="max-w-xs truncate font-medium text-ink">
                  {{ item.title }}
                </p>
              </div>
            </td>

            <!-- Categoría -->
            <td class="px-4 py-3 text-muted">
              {{ item.category_name }}
              <span class="ml-1 text-xs" :class="item.visibility === 'private' ? 'text-amber-700' : 'text-sky-600'">
                · {{ item.visibility === "private" ? "Privado" : "Público" }}
              </span>
            </td>

            <!-- Autor -->
            <td class="px-4 py-3 text-muted">
              {{ item.author_name }}
            </td>

            <!-- Estado -->
            <td class="px-4 py-3">
              <span
                class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                :class="STATUS_BADGE_CLASS[item.status]"
              >
                {{ STATUS_LABELS[item.status] }}
              </span>
            </td>

            <!-- Comentarios -->
            <td class="px-4 py-3">
              <NuxtLink
                :to="`/blog/${item.slug}`"
                target="_blank"
                class="inline-flex items-center gap-1 text-muted hover:text-gold"
              >
                <AppIcon name="message" :size="14" />
                {{ item.comments_count }}
              </NuxtLink>
            </td>

            <!-- Acciones -->
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <NuxtLink
                  :to="`/blog/${item.slug}`"
                  target="_blank"
                  class="btn-outline !px-2 !py-1 text-xs"
                >
                  Ver
                </NuxtLink>

                <button v-if="authStore.can('blog', 'edit', item.category_slug)" class="btn-outline !px-2 !py-1 text-xs" @click="openEdit(item)">
                  Editar
                </button>

                <button
                  v-if="item.status === 'IN_REVIEW' && authStore.can('blog', 'approve', item.category_slug)"
                  class="btn-outline !px-2 !py-1 text-xs !text-emerald-600"
                  :disabled="actingSlug === item.slug"
                  @click="approve(item)"
                >
                  Aprobar
                </button>

                <button
                  v-if="item.status === 'IN_REVIEW' && authStore.can('blog', 'approve', item.category_slug)"
                  class="btn-outline !px-2 !py-1 text-xs !text-amber-600"
                  :disabled="actingSlug === item.slug"
                  @click="reject(item)"
                >
                  Rechazar
                </button>

                <button
                  v-if="authStore.can('blog', 'delete', item.category_slug)"
                  class="btn-outline !px-2 !py-1 text-xs !text-rose-500"
                  :disabled="actingSlug === item.slug"
                  @click="remove(item)"
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="!posts.length" class="py-8 text-center text-sm text-muted">
        No hay blogs con este filtro.
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
