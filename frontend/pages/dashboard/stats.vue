<script setup lang="ts">
import { reviewService } from "~/services/review.service";
import type { Review } from "~/types";

definePageMeta({ layout: "dashboard", middleware: "auth" });

const businessStore = useBusinessStore();
const questionsStore = useQuestionsStore();
await businessStore.fetchMyBusinesses();
await questionsStore.fetchMyQuestions();
const business = computed(() => businessStore.primaryBusiness);

const reviews = ref<Review[]>([]);

if (business.value) {
  const { data } = await reviewService.listByBusiness(business.value.id, { page_size: 100 });
  reviews.value = data.results;
}

const ratingDistribution = computed(() => {
  const counts = [0, 0, 0, 0, 0];
  reviews.value.forEach((r) => {
    if (r.rating >= 1 && r.rating <= 5) counts[r.rating - 1] += 1;
  });
  const max = Math.max(...counts, 1);
  return counts.map((count, index) => ({ stars: index + 1, count, pct: (count / max) * 100 }));
});
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Estadísticas</h1>
    <p class="mt-1 text-sm text-muted">Un resumen real del desempeño de tu emprendimiento.</p>

    <EmptyState v-if="!business" icon="briefcase" title="Primero crea tu emprendimiento" class="mt-8">
      <NuxtLink to="/dashboard/business" class="btn-primary mt-2">Crear emprendimiento</NuxtLink>
    </EmptyState>

    <template v-else>
      <div class="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Rating promedio" :value="business.average_rating" icon="star" />
        <StatCard label="Opiniones totales" :value="reviews.length" icon="message" />
        <StatCard label="Fotos en galería" :value="`${business.images?.length ?? 0}/4`" icon="images" />
        <StatCard label="Preguntas respondidas" :value="`${questionsStore.myQuestions.length - questionsStore.pendingCount}/${questionsStore.myQuestions.length}`" icon="check-circle" />
      </div>

      <div class="card mt-6 p-5">
        <p class="font-semibold text-ink">Distribución de calificaciones</p>
        <div class="mt-4 space-y-2">
          <div v-for="row in [...ratingDistribution].reverse()" :key="row.stars" class="flex items-center gap-3">
            <span class="w-10 shrink-0 text-sm text-muted">{{ row.stars }} ★</span>
            <div class="h-2.5 flex-1 overflow-hidden rounded-full bg-line">
              <div class="h-full rounded-full bg-gold" :style="{ width: row.pct + '%' }" />
            </div>
            <span class="w-8 shrink-0 text-right text-sm text-muted">{{ row.count }}</span>
          </div>
        </div>
        <p v-if="!reviews.length" class="mt-4 text-sm text-muted">Todavía no tienes opiniones para mostrar estadísticas.</p>
      </div>
    </template>
  </div>
</template>
