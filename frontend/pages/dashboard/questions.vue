<script setup lang="ts">
definePageMeta({ layout: "dashboard", middleware: "auth" });

const questionsStore = useQuestionsStore();
await questionsStore.fetchMyQuestions();

const filter = ref<"all" | "pending" | "answered">("all");
const filtered = computed(() => {
  if (filter.value === "pending") return questionsStore.myQuestions.filter((q) => !q.answer);
  if (filter.value === "answered") return questionsStore.myQuestions.filter((q) => q.answer);
  return questionsStore.myQuestions;
});
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Preguntas</h1>
    <p class="mt-1 text-sm text-muted">Responde las preguntas de tu comunidad.</p>

    <div class="mt-4 flex gap-2">
      <button class="btn-outline" :class="filter === 'all' && '!border-pink !text-pink'" @click="filter = 'all'">Todas</button>
      <button class="btn-outline" :class="filter === 'pending' && '!border-pink !text-pink'" @click="filter = 'pending'">
        Sin responder ({{ questionsStore.pendingCount }})
      </button>
      <button class="btn-outline" :class="filter === 'answered' && '!border-pink !text-pink'" @click="filter = 'answered'">Respondidas</button>
    </div>

    <div class="card mt-6 p-5">
      <LoadingSpinner v-if="questionsStore.loading" />
      <template v-else>
        <QuestionItem
          v-for="question in filtered"
          :key="question.id"
          :question="question"
          :can-answer="true"
          @answer="(id, text) => questionsStore.answer(id, text)"
        />
        <p v-if="!filtered.length" class="py-6 text-center text-sm text-muted">No hay preguntas en esta categoría.</p>
      </template>
    </div>
  </div>
</template>
