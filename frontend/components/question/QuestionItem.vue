<script setup lang="ts">
import type { Question } from "~/types";

defineProps<{ question: Question; canAnswer?: boolean }>();
const emit = defineEmits<{ (e: "answer", questionId: number, text: string): void }>();

const answerText = ref("");
const submitting = ref(false);

function submit(questionId: number) {
  if (!answerText.value.trim()) return;
  submitting.value = true;
  emit("answer", questionId, answerText.value.trim());
  answerText.value = "";
  submitting.value = false;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}
</script>

<template>
  <div class="border-b border-line py-4 last:border-0">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-start gap-3">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-pink-light text-sm font-semibold text-pink">
          {{ question.user_name?.charAt(0) || "?" }}
        </span>
        <div>
          <p class="text-sm font-semibold text-ink">{{ question.user_name }}</p>
          <p class="mt-0.5 text-sm text-ink">{{ question.question }}</p>
        </div>
      </div>
      <span class="shrink-0 text-xs text-muted">{{ formatDate(question.created_at) }}</span>
    </div>

    <div v-if="question.answer" class="ml-12 mt-3 rounded-xl2 bg-pink-light/50 p-3">
      <p class="text-xs font-semibold text-pink">Respuesta</p>
      <p class="mt-1 text-sm text-ink">{{ question.answer.answer }}</p>
    </div>

    <div v-else-if="canAnswer" class="ml-12 mt-3 flex gap-2">
      <input v-model="answerText" type="text" class="field" placeholder="Escribe una respuesta..." />
      <button class="btn-primary shrink-0" :disabled="submitting" @click="submit(question.id)">Responder</button>
    </div>
  </div>
</template>
