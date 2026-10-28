<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { Question } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const questions = ref<Question[]>([]);
const drafts = reactive<Record<number, string>>({});
const error = ref("");

const { businessId } = usePortalBusiness(async (id) => {
  questions.value = (await portalService.questions(id)).data.results;
});

async function answer(question: Question) {
  error.value = "";
  try {
    const { data } = await portalService.answer(businessId.value, question.id, drafts[question.id] ?? "");
    Object.assign(question, data);
    delete drafts[question.id];
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Preguntas</h1>
      <p class="text-sm text-muted">Lo que te preguntan las usuarias en tu página.</p>
    </header>
    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
    <EmptyState v-if="!questions.length" icon="message" title="Aún no tienes preguntas" />

    <article v-for="question in questions" :key="question.id" class="card space-y-2 p-5">
      <p class="text-xs text-muted">{{ question.user_name }} · {{ new Date(question.created_at).toLocaleDateString("es-CO") }}</p>
      <p class="font-medium text-ink">{{ question.question }}</p>
      <p v-if="question.answer" class="rounded-xl2 bg-gold-light/40 p-3 text-sm text-ink">{{ question.answer.answer }}</p>
      <form class="flex gap-2" @submit.prevent="answer(question)">
        <input v-model="drafts[question.id]" class="input" :placeholder="question.answer ? 'Editar respuesta...' : 'Escribe tu respuesta...'" />
        <button class="btn-primary" :disabled="!(drafts[question.id] ?? '').trim()">Responder</button>
      </form>
    </article>
  </div>
</template>
