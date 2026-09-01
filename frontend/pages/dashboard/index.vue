<script setup lang="ts">
import { reviewService } from "~/services/review.service";
import type { Review } from "~/types";

definePageMeta({ layout: "dashboard", middleware: "entrepreneur" });

const businessStore = useBusinessStore();
const questionsStore = useQuestionsStore();

await businessStore.fetchMyBusinesses();
await questionsStore.fetchMyQuestions();

const business = computed(() => businessStore.primaryBusiness);
const reviews = ref<Review[]>([]);

if (business.value) {
  const { data } = await reviewService.listByBusiness(business.value.id);
  reviews.value = data.results;
}

const answeredCount = computed(() => questionsStore.myQuestions.filter((q) => q.answer).length);
const imagesCount = computed(() => business.value?.images?.length ?? 0);
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-ink">Mi emprendimiento</h1>
        <p class="mt-1 text-sm text-muted">Aquí tienes un resumen de tu emprendimiento.</p>
      </div>
      <NuxtLink v-if="business" to="/dashboard/business" class="btn-primary">Editar perfil</NuxtLink>
    </div>

    <EmptyState
      v-if="!business"
      icon="briefcase"
      title="Aún no tienes un emprendimiento"
      description="Crea tu perfil para empezar a recibir preguntas y opiniones de la comunidad."
      class="mt-8"
    >
      <NuxtLink to="/dashboard/business" class="btn-primary mt-2">Crear mi emprendimiento</NuxtLink>
    </EmptyState>

    <template v-else>
      <div
        v-if="business.status !== 'approved'"
        class="mt-6 rounded-xl2 border p-4 text-sm"
        :class="business.status === 'pending' ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-rose-200 bg-rose-50 text-rose-700'"
      >
        <span v-if="business.status === 'pending'">Tu emprendimiento está en revisión. Te avisaremos cuando sea aprobado.</span>
        <span v-else>Tu emprendimiento fue rechazado. Revisa la información y actualízala desde "Mi emprendimiento".</span>
      </div>

      <div class="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Preguntas" :value="questionsStore.myQuestions.length" icon="message" :trend="`${answeredCount} respondidas`" />
        <StatCard label="Sin responder" :value="questionsStore.pendingCount" icon="clock" :trend-positive="false" />
        <StatCard label="Fotos en galería" :value="`${imagesCount}/4`" icon="images" />
        <StatCard label="Opiniones" :value="reviews.length" icon="star" :trend="`${business.average_rating} ★ promedio`" />
      </div>

      <div class="mt-8 card p-5">
        <p class="font-semibold text-ink">Preguntas recientes</p>
        <div v-if="questionsStore.myQuestions.length" class="mt-2">
          <QuestionItem
            v-for="question in questionsStore.myQuestions.slice(0, 5)"
            :key="question.id"
            :question="question"
            :can-answer="true"
            @answer="(id, text) => questionsStore.answer(id, text)"
          />
        </div>
        <p v-else class="mt-2 text-sm text-muted">Todavía no tienes preguntas.</p>
      </div>
    </template>
  </div>
</template>
