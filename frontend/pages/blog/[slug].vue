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
  throw createError({ statusCode: 404, statusMessage: "Artículo no encontrado" });
}

const comments = ref<BlogComment[]>([]);
const loadingComments = ref(false);

async function loadComments() {
  loadingComments.value = true;
  try {
    const { data } = await blogService.comments(slug);
    comments.value = data.results;
  } finally {
    loadingComments.value = false;
  }
}
await loadComments();

const newComment = ref("");
const submittingComment = ref(false);
const commentError = ref("");

async function submitComment() {
  if (!authStore.isAuthenticated) {
    return navigateTo(`/login?redirect=/blog/${slug}`);
  }

  if (!newComment.value.trim()) return;

  submittingComment.value = true;
  commentError.value = "";

  try {
    const { data } = await blogService.addComment(slug, newComment.value.trim());
    comments.value = [data, ...comments.value];
    newComment.value = "";
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
      <h2 class="font-semibold text-ink">Comentarios ({{ comments.length }})</h2>

      <div v-if="authStore.isAuthenticated" class="mt-4 card p-4">
        <textarea
          v-model="newComment"
          rows="3"
          class="field"
          placeholder="Comparte lo que piensas sobre este artículo..."
        />
        <p v-if="commentError" class="mt-1 text-xs text-rose-500">{{ commentError }}</p>
        <button
          class="btn-primary mt-2"
          :disabled="submittingComment || !newComment.trim()"
          @click="submitComment"
        >
          {{ submittingComment ? "Publicando..." : "Comentar" }}
        </button>
      </div>

      <p v-else class="mt-4 text-sm text-muted">
        <NuxtLink :to="`/login?redirect=/blog/${slug}`" class="text-gold hover:underline">Inicia sesión</NuxtLink>
        para dejar un comentario.
      </p>

      <LoadingSpinner v-if="loadingComments" />
      <div v-else class="mt-4">
        <BlogCommentItem v-for="comment in comments" :key="comment.id" :comment="comment" />
        <p v-if="!comments.length" class="py-6 text-sm text-muted">Sé la primera persona en comentar.</p>
      </div>
    </div>
  </div>
</template>
