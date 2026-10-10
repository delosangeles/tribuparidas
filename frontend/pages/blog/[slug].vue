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

    <img
      v-if="post.main_image"
      :src="post.main_image"
      :alt="post.title"
      class="mt-6 aspect-video w-full rounded-xl2 object-cover"
    />

    <p class="mt-6 text-base font-medium text-ink">{{ post.summary }}</p>

    <div class="prose prose-sm mt-6 max-w-none whitespace-pre-line text-sm text-ink">{{ post.content }}</div>

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
