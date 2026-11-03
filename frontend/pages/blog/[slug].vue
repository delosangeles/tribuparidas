<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import type { BlogComment } from "~/types";

const route = useRoute();
const slug = route.params.slug as string;
const authStore = useAuthStore();

const { data: post, error } = await useAsyncData(`blog-post-${slug}`, async () => {
  const { data } = await blogService.retrieve(slug);
  return data;
});

if (error.value) {
  // Sin sesión un blog privado responde 404: se invita a iniciar sesión por si es privado.
  if (!authStore.isAuthenticated) {
    await navigateTo(`/login?redirect=/blog/${slug}`);
  } else {
    throw createError({ statusCode: 404, statusMessage: "Artículo no encontrado" });
  }
}

// Me gusta y lecturas del artículo.
const liked = ref(post.value?.liked_by_me ?? false);
const likesCount = ref(post.value?.likes_count ?? 0);
const readsCount = ref(post.value?.reads_count ?? 0);
const likeBusy = ref(false);

async function togglePostLike() {
  if (!authStore.isAuthenticated) {
    return navigateTo(`/login?redirect=/blog/${slug}`);
  }
  if (likeBusy.value) return;
  likeBusy.value = true;
  const before = { liked: liked.value, count: likesCount.value };
  liked.value = !before.liked;
  likesCount.value = before.count + (before.liked ? -1 : 1);
  try {
    const { data } = await blogService.togglePostLike(slug);
    liked.value = data.liked;
    likesCount.value = data.likes_count;
  } catch {
    liked.value = before.liked;
    likesCount.value = before.count;
  } finally {
    likeBusy.value = false;
  }
}

// Cuenta como "leído" tras 60 s con la pestaña visible. Se avisa al abrir y
// otra vez al cumplir el minuto; el servidor mide el tiempo y decide.
const READ_SECONDS = 60;
let readTimer: ReturnType<typeof setInterval> | null = null;

function stopReadTimer() {
  if (readTimer) clearInterval(readTimer);
  readTimer = null;
}

onMounted(async () => {
  if (!post.value || !authStore.isAuthenticated) return;
  try {
    await blogService.markRead(slug);
  } catch {
    return;
  }
  let visibleSeconds = 0;
  let asked = false;
  readTimer = setInterval(async () => {
    if (document.visibilityState !== "visible" || asked) return;
    visibleSeconds += 1;
    if (visibleSeconds < READ_SECONDS) return;
    asked = true;
    try {
      const { data } = await blogService.markRead(slug);
      readsCount.value = data.reads_count;
      if (data.read) stopReadTimer();
      else asked = false; // el reloj del servidor aún no llega al minuto: reintentar
    } catch {
      asked = false;
    }
  }, 1000);
});

onBeforeUnmount(stopReadTimer);

const comments = ref<BlogComment[]>([]);
const loadingComments = ref(false);

async function loadComments() {
  if (!post.value) return; // redirigido al login (blog privado)
  try {
    const { data } = await blogService.comments(slug, { page_size: 100 });
    comments.value = data.results;
  } finally {
    loadingComments.value = false;
  }
}
loadingComments.value = true;
await loadComments();

// Comentarios principales + respuestas.
const totalComments = computed(() => comments.value.reduce((total, c) => total + 1 + (c.replies?.length ?? 0), 0));

const composer = ref<{ reset: () => void } | null>(null);
const submittingComment = ref(false);
const commentError = ref("");

async function submitComment(payload: { content: string; image: File | null }) {
  if (!authStore.isAuthenticated) {
    return navigateTo(`/login?redirect=/blog/${slug}`);
  }

  submittingComment.value = true;
  commentError.value = "";

  try {
    await blogService.addComment(slug, payload);
    composer.value?.reset();
    await loadComments();
  } catch (err) {
    commentError.value = useErrorMessage(err);
  } finally {
    submittingComment.value = false;
  }
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
}
</script>

<template>
  <div v-if="post" class="mx-auto max-w-3xl px-4 py-8 sm:px-6">
    <nav class="mb-4 flex flex-wrap items-center gap-1 text-xs text-muted">
      <NuxtLink to="/" class="hover:text-gold">Inicio</NuxtLink>
      <span>/</span>
      <NuxtLink to="/blog" class="hover:text-gold">Blog</NuxtLink>
      <span>/</span>
      <NuxtLink :to="`/blog?category=${post.category_slug}`" class="hover:text-gold">{{ post.category_name }}</NuxtLink>
      <span>/</span>
      <span class="text-ink">{{ post.title }}</span>
    </nav>

    <div class="flex flex-wrap items-center gap-2">
      <span class="badge bg-gold-light text-gold">{{ post.category_name }}</span>
      <span v-if="post.visibility === 'private'" class="badge bg-amber-50 text-amber-700">🔒 Solo tribu</span>
      <span v-for="stage in post.stages_detail" :key="stage.id" class="badge bg-gold-light text-gold">
        {{ stage.name }}
      </span>
      <span v-if="post.featured" class="badge bg-gold-light text-gold">Destacado</span>
    </div>

    <h1 class="mt-3 text-2xl font-bold text-ink sm:text-3xl">{{ post.title }}</h1>

    <div class="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted">
      <span>{{ post.author_name }}</span>
      <template v-if="post.publication_date">
        <span>·</span>
        <span>{{ formatDate(post.publication_date) }}</span>
      </template>
      <span>·</span>
      <span>{{ post.reading_time }} min de lectura</span>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted">
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 transition hover:border-rose-300 hover:text-rose-500"
        :class="liked ? '!border-rose-300 text-rose-500' : ''"
        :aria-pressed="liked"
        :aria-label="liked ? 'Quitar me gusta' : 'Me gusta'"
        @click="togglePostLike"
      >
        <AppIcon name="heart" :size="16" :class="liked ? 'fill-current' : ''" />
        <span>{{ likesCount }}</span>
      </button>
      <span v-if="readsCount">
        {{ readsCount }} {{ readsCount === 1 ? "persona lo ha leído" : "personas lo han leído" }}
      </span>
    </div>

    <img
      v-if="post.main_image"
      :src="post.main_image"
      :alt="post.title"
      class="mt-6 aspect-video w-full rounded-xl2 object-cover"
    />

    <p class="mt-6 text-base font-medium text-ink">{{ post.summary }}</p>

    <div class="rich-content mt-6 text-sm text-ink" v-html="contentToHtml(post.content)" />

    <div v-if="post.sources" class="mt-8 rounded-xl2 border border-line p-4">
      <p class="text-sm font-semibold text-ink">Fuentes</p>
      <p class="mt-1 whitespace-pre-line text-sm text-muted">{{ post.sources }}</p>
    </div>

    <!-- Comentarios -->
    <div class="mt-10 border-t border-line pt-8">
      <h2 class="font-semibold text-ink">Comentarios ({{ totalComments }})</h2>

      <div v-if="authStore.isAuthenticated" class="mt-4">
        <CommentComposer
          ref="composer"
          placeholder="Comparte lo que piensas sobre este artículo..."
          submit-label="Comentar"
          :busy="submittingComment"
          :error="commentError"
          @submit="submitComment"
        />
      </div>

      <p v-else class="mt-4 text-sm text-muted">
        <NuxtLink :to="`/login?redirect=/blog/${slug}`" class="text-gold hover:underline">Inicia sesión</NuxtLink>
        para dejar un comentario.
      </p>

      <LoadingSpinner v-if="loadingComments" />
      <div v-else class="mt-4">
        <BlogCommentItem v-for="comment in comments" :key="comment.id" :comment="comment" :slug="slug" @changed="loadComments" />
        <p v-if="!comments.length" class="py-6 text-sm text-muted">Sé la primera persona en comentar.</p>
      </div>
    </div>
  </div>
</template>
