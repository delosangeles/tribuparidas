import { defineStore } from "pinia";
import { questionService } from "~/services/question.service";
import type { Question } from "~/types";

export const useQuestionsStore = defineStore("questions", () => {
  const myQuestions = ref<Question[]>([]);
  const loading = ref(false);

  const pendingCount = computed(() => myQuestions.value.filter((q) => !q.answer).length);

  async function fetchMyQuestions() {
    loading.value = true;
    try {
      const { data } = await questionService.myQuestions({ page_size: 50 });
      myQuestions.value = data.results;
    } finally {
      loading.value = false;
    }
  }

  async function answer(questionId: number, text: string) {
    const { data } = await questionService.answer(questionId, text);
    const target = myQuestions.value.find((q) => q.id === questionId);
    if (target) target.answer = data;
  }

  return { myQuestions, loading, pendingCount, fetchMyQuestions, answer };
});
