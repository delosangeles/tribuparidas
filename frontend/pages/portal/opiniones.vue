<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalReview } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const reviews = ref<PortalReview[]>([]);
const page = ref(1);
const hasNext = ref(false);
const hasPrevious = ref(false);
const error = ref("");
const replying = ref<number | null>(null);
const draft = ref("");

const { businessId } = usePortalBusiness(() => {
  page.value = 1;
  return load();
});

async function load() {
  const { data } = await portalService.reviews(businessId.value, { page: page.value });
  reviews.value = data.results;
  hasNext.value = Boolean(data.next);
  hasPrevious.value = Boolean(data.previous);
}
watch(page, load);

function startReply(review: PortalReview) {
  replying.value = review.id;
  draft.value = review.reply?.text ?? "";
}

async function sendReply(review: PortalReview) {
  error.value = "";
  try {
    const { data } = await portalService.reply(businessId.value, review.id, draft.value);
    review.reply = data.reply;
    replying.value = null;
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

async function removeReply(review: PortalReview) {
  await portalService.deleteReply(businessId.value, review.id);
  review.reply = null;
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Opiniones</h1>
      <p class="text-sm text-muted">Lo que dicen de tu emprendimiento. Las opiniones no se pueden editar ni borrar, pero puedes responderlas.</p>
    </header>
    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
    <EmptyState v-if="!reviews.length" icon="star" title="Aún no tienes opiniones" />

    <article v-for="review in reviews" :key="review.id" class="card space-y-2 p-5">
      <div class="flex items-center justify-between">
        <p class="font-medium text-ink">{{ review.user_name }}</p>
        <StarRating :rating="review.rating" />
      </div>
      <p v-if="review.comment" class="text-sm text-muted">{{ review.comment }}</p>
      <p class="text-xs text-muted">{{ new Date(review.created_at).toLocaleDateString("es-CO") }}</p>

      <div v-if="review.reply && replying !== review.id" class="rounded-xl2 bg-gold-light/40 p-3">
        <p class="text-xs font-semibold text-gold-dark">Tu respuesta</p>
        <p class="text-sm text-ink">{{ review.reply.text }}</p>
        <div class="mt-1 flex gap-1">
          <button class="btn-ghost !px-2 !py-1 text-xs" @click="startReply(review)">Editar</button>
          <button class="btn-ghost !px-2 !py-1 text-xs !text-rose-500" @click="removeReply(review)">Quitar</button>
        </div>
      </div>
      <form v-else-if="replying === review.id" class="space-y-2" @submit.prevent="sendReply(review)">
        <textarea v-model="draft" rows="3" maxlength="1000" class="field" placeholder="Escribe tu respuesta..." />
        <div class="flex gap-2">
          <button class="btn-primary" :disabled="!draft.trim()">Responder</button>
          <button type="button" class="btn-ghost" @click="replying = null">Cancelar</button>
        </div>
      </form>
      <button v-else class="btn-outline" @click="startReply(review)">Responder</button>
    </article>

    <Pagination v-model:page="page" :has-next="hasNext" :has-previous="hasPrevious" />
  </div>
</template>
