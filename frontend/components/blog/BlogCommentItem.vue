<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import type { BlogComment } from "~/types";

// Un comentario del blog con foto, "me gusta", respuestas (un nivel), edición
// de la propia autora y eliminación (autora o admin). Después de cada cambio
// avisa con `changed` para que la página vuelva a cargar los comentarios.
const props = defineProps<{ comment: BlogComment; slug: string; isReply?: boolean }>();
const emit = defineEmits<{ (e: "changed"): void }>();

const authStore = useAuthStore();
const isAuthor = computed(() => authStore.user?.id === props.comment.author);
const canDelete = computed(() => isAuthor.value || authStore.isAdmin);
const loginUrl = computed(() => `/login?redirect=/blog/${props.slug}`);

const mode = ref<"view" | "edit" | "reply">("view");
const busy = ref(false);
const actionError = ref("");
const confirmingDelete = ref(false);

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}

// ---- me gusta (se actualiza al instante y se corrige si falla)
const liked = ref(props.comment.liked_by_me);
const likeCount = ref(props.comment.like_count);
watch(
  () => props.comment,
  (comment) => {
    liked.value = comment.liked_by_me;
    likeCount.value = comment.like_count;
  }
);

async function toggleLike() {
  if (!authStore.isAuthenticated) return navigateTo(loginUrl.value);
  const before = { liked: liked.value, count: likeCount.value };
  liked.value = !before.liked;
  likeCount.value = before.count + (before.liked ? -1 : 1);
  try {
    const { data } = await blogService.toggleLike(props.slug, props.comment.id);
    liked.value = data.liked;
    likeCount.value = data.like_count;
  } catch {
    liked.value = before.liked;
    likeCount.value = before.count;
  }
}

// ---- responder / editar / eliminar
const replyStart = computed(() => (props.isReply ? `@${props.comment.author_name.split(" ")[0]} ` : ""));

async function run(task: () => Promise<unknown>) {
  busy.value = true;
  actionError.value = "";
  try {
    await task();
    mode.value = "view";
    emit("changed");
  } catch (err) {
    actionError.value = useErrorMessage(err);
  } finally {
    busy.value = false;
  }
}

function submitReply(payload: { content: string; image: File | null }) {
  return run(() => blogService.addComment(props.slug, { ...payload, parent: props.comment.id }));
}

function submitEdit(payload: { content: string; image: File | null; removeImage: boolean }) {
  return run(() => blogService.updateComment(props.slug, props.comment.id, payload));
}

async function confirmDelete() {
  confirmingDelete.value = false;
  await run(() => blogService.deleteComment(props.slug, props.comment.id));
}
</script>

<template>
  <div class="py-4" :class="isReply ? '' : 'border-b border-line last:border-0'">
    <div class="flex items-start gap-3">
      <UserAvatar :src="comment.author_photo" :name="comment.author_name" :size="isReply ? 'sm' : 'md'" />

      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-baseline justify-between gap-x-3">
          <p class="text-sm font-semibold text-ink">{{ comment.author_name }}</p>
          <span class="text-xs text-muted">
            {{ formatDate(comment.created_at) }}<template v-if="comment.edited_at"> · editado</template>
          </span>
        </div>

        <!-- edición -->
        <div v-if="mode === 'edit'" class="mt-2">
          <CommentComposer
            submit-label="Guardar"
            :initial-text="comment.content"
            :initial-image="comment.image"
            :busy="busy"
            :error="actionError"
            cancelable
            :rows="3"
            @submit="submitEdit"
            @cancel="mode = 'view'"
          />
        </div>

        <!-- lectura -->
        <template v-else>
          <p v-if="comment.content" class="mt-1 whitespace-pre-line text-sm text-ink">{{ comment.content }}</p>
          <a v-if="comment.image" :href="comment.image" target="_blank" rel="noopener" class="mt-2 block w-fit">
            <img :src="comment.image" alt="Foto del comentario" class="max-h-72 max-w-full rounded-xl2 border border-line object-cover" loading="lazy" />
          </a>

          <div class="mt-2 flex flex-wrap items-center gap-1 text-xs text-muted">
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-full px-2 py-1 transition hover:bg-rose-50 hover:text-rose-500"
              :class="liked ? 'text-rose-500' : ''"
              :aria-pressed="liked"
              :aria-label="liked ? 'Quitar me gusta' : 'Me gusta'"
              @click="toggleLike"
            >
              <AppIcon name="heart" :size="14" :class="liked ? 'fill-current' : ''" />
              <span v-if="likeCount">{{ likeCount }}</span>
              <span v-else>Me gusta</span>
            </button>
            <button v-if="authStore.isAuthenticated" type="button" class="rounded-full px-2 py-1 transition hover:bg-gold-light hover:text-gold" @click="mode = mode === 'reply' ? 'view' : 'reply'">
              Responder
            </button>
            <NuxtLink v-else :to="loginUrl" class="rounded-full px-2 py-1 transition hover:bg-gold-light hover:text-gold">
              Inicia sesión para responder
            </NuxtLink>
            <button v-if="isAuthor" type="button" class="inline-flex items-center gap-1 rounded-full px-2 py-1 transition hover:bg-gold-light hover:text-gold" @click="mode = 'edit'">
              <AppIcon name="edit" :size="12" /> Editar
            </button>
            <button v-if="canDelete" type="button" class="inline-flex items-center gap-1 rounded-full px-2 py-1 transition hover:bg-rose-50 hover:text-rose-500" @click="confirmingDelete = true">
              <AppIcon name="trash" :size="12" /> Eliminar<template v-if="!isAuthor"> (admin)</template>
            </button>
          </div>
          <p v-if="actionError && mode === 'view'" class="mt-1 text-xs text-rose-500">{{ actionError }}</p>
        </template>

        <!-- responder -->
        <div v-if="mode === 'reply'" class="mt-2">
          <CommentComposer
            :key="`reply-${comment.id}`"
            :placeholder="`Responder a ${comment.author_name}...`"
            submit-label="Responder"
            :initial-text="replyStart"
            :busy="busy"
            :error="actionError"
            cancelable
            :rows="2"
            @submit="submitReply"
            @cancel="mode = 'view'"
          />
        </div>

        <!-- respuestas -->
        <div v-if="comment.replies?.length" class="mt-2 border-l-2 border-gold-light pl-3 sm:pl-4">
          <BlogCommentItem v-for="reply in comment.replies" :key="reply.id" :comment="reply" :slug="slug" is-reply @changed="emit('changed')" />
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="confirmingDelete"
      :title="isAuthor ? '¿Eliminar tu comentario?' : '¿Eliminar este comentario?'"
      :description="comment.replies?.length ? 'También se eliminarán sus respuestas. No se puede deshacer.' : 'No se puede deshacer.'"
      confirm-label="Eliminar"
      danger
      @confirm="confirmDelete"
      @cancel="confirmingDelete = false"
    />
  </div>
</template>
