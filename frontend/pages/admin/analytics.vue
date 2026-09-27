<script setup lang="ts">
import { analyticsService } from "~/services/analytics.service";

definePageMeta({ layout: "admin", middleware: "superadmin" });

const { data, pending } = await useAsyncData("admin-analytics", async () => {
  const { data } = await analyticsService.summary();
  return data;
});

function formatDay(day: string) {
  return new Date(`${day}T00:00:00`).toLocaleDateString("es-CO", { day: "numeric", month: "short" });
}

// "Vistas por día" arranca en la semana actual (últimos 7 días); el backend
// manda hasta 31 días para poder ver también el mes completo sin otro request.
const dayRange = ref<"week" | "month">("week");

const byDayItems = computed(() => {
  const all = data.value?.by_day || [];
  const sliced = dayRange.value === "week" ? all.slice(-7) : all.slice(-31);
  return sliced.map((d) => ({ label: formatDay(d.day), value: d.count }));
});
const byHourItems = computed(() => (data.value?.by_hour || []).map((h) => ({ label: `${h.hour}h`, value: h.count })));
const topPagesItems = computed(() => (data.value?.top_pages || []).map((p) => ({ label: p.path, value: p.count, href: p.path })));
const lastPagesItems = computed(() => (data.value?.last_pages || []).map((p) => ({ label: p.path, value: p.count, href: p.path })));
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Analítica del sitio</h1>
    <p class="mt-1 text-sm text-muted">
      Cuándo se conecta la gente, qué páginas visitan y hasta dónde llegan. Últimos 14 días.
      No incluye login, registro ni el panel admin.
    </p>

    <LoadingSpinner v-if="pending" />
    <template v-else>
      <div class="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Vistas de página" :value="data?.total_pageviews ?? 0" icon="chart" />
        <StatCard label="Visitas (sesiones)" :value="data?.unique_sessions ?? 0" icon="users" />
        <StatCard label="Usuarias distintas" :value="data?.unique_users ?? 0" icon="heart" />
      </div>

      <div class="mt-8 card p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="font-semibold text-ink">Vistas por día</p>

          <div class="flex gap-2">
            <button
              type="button"
              class="btn-outline !px-3 !py-1 text-xs"
              :class="dayRange === 'week' && '!border-gold !text-gold'"
              @click="dayRange = 'week'"
            >
              Semana
            </button>
            <button
              type="button"
              class="btn-outline !px-3 !py-1 text-xs"
              :class="dayRange === 'month' && '!border-gold !text-gold'"
              @click="dayRange = 'month'"
            >
              Mes
            </button>
          </div>
        </div>
        <div class="mt-4">
          <BarChart :items="byDayItems" orientation="vertical" />
        </div>
      </div>

      <div class="mt-6 card p-5">
        <p class="font-semibold text-ink">A qué hora se conecta la gente</p>
        <p class="mt-1 text-xs text-muted">Hora local del navegador, sumado en todas las visitas.</p>
        <div class="mt-4">
          <BarChart :items="byHourItems" orientation="vertical" />
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="card p-5">
          <p class="font-semibold text-ink">Páginas más visitadas</p>
          <p class="mt-1 text-xs text-muted">Toca una página para abrirla.</p>
          <div class="mt-4">
            <BarChart :items="topPagesItems" orientation="horizontal" />
          </div>
        </div>

        <div class="card p-5">
          <p class="font-semibold text-ink">Hasta dónde llegan (última página de cada visita)</p>
          <p class="mt-1 text-xs text-muted">Toca una página para abrirla.</p>
          <div class="mt-4">
            <BarChart :items="lastPagesItems" orientation="horizontal" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
