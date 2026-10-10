<script setup lang="ts">
import { analyticsService } from "~/services/analytics.service";
import type { MonthlyReport } from "~/types";

definePageMeta({ layout: "admin", middleware: "superadmin" });

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

// Los reportes se generan solos el día 1 de cada mes (el del mes anterior) y
// quedan guardados: aquí solo se consultan, no se recalculan.
const { data: reports, pending, error } = await useAsyncData("monthly-reports", async () => {
  const { data } = await analyticsService.monthlyReports();
  return data;
});

const selectedId = ref<number | null>(reports.value?.[0]?.id ?? null);
const report = computed<MonthlyReport | null>(() => reports.value?.find((r) => r.id === selectedId.value) ?? null);

const monthName = (r: MonthlyReport) => `${MESES[r.month - 1]} ${r.year}`;

function formatDay(iso: string, short = false) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", short ? { day: "numeric" } : { day: "numeric", month: "short" }).format(new Date(y, m - 1, d));
}

const generatedLabel = computed(() =>
  report.value
    ? new Intl.DateTimeFormat("es-CO", { dateStyle: "long", timeStyle: "short" }).format(new Date(report.value.generated_at))
    : ""
);

const dayValues = computed(() => report.value?.data.days.map((d) => d.pageviews) ?? []);
const dayLabels = computed(() => report.value?.data.days.map((d) => formatDay(d.date, true)) ?? []);
const hourValues = computed(() => report.value?.data.by_hour.map((h) => h.count) ?? []);
const hourLabels = computed(() => report.value?.data.by_hour.map((h) => `${h.hour}h`) ?? []);
const registrationValues = computed(() => report.value?.data.days.map((d) => d.users) ?? []);

// Qué gráfica acompaña a cada párrafo del reporte.
function chartFor(title: string) {
  if (title === "Usuarias") return { values: registrationValues.value, labels: dayLabels.value, title: "Registros por día" };
  if (title === "Visitas" || title === "Mejor día") return { values: dayValues.value, labels: dayLabels.value, title: "Visitas por día" };
  if (title === "Mejor hora") return { values: hourValues.value, labels: hourLabels.value, title: "Visitas por hora" };
  return null;
}

const copied = ref(false);
async function copyReport() {
  if (!report.value) return;
  const body = report.value.data.sections.map((s) => `${s.title}\n${s.text}`).join("\n\n");
  await navigator.clipboard.writeText(`Tribu Paridas · ${monthName(report.value)}\n\n${body}`);
  copied.value = true;
  setTimeout(() => (copied.value = false), 2000);
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Reportes mensuales</h1>
    <p class="mt-1 text-sm text-muted">
      El día 1 de cada mes se genera el reporte del mes anterior. Una vez generado queda guardado y no se vuelve a calcular. Solo lo ve el Super Admin.
    </p>

    <p v-if="error" class="mt-4 text-sm text-rose-500">No se pudieron cargar los reportes. Intenta de nuevo.</p>
    <LoadingSpinner v-if="pending" />

    <EmptyState
      v-else-if="!reports?.length"
      icon="chart"
      title="Aún no hay reportes"
      description="El primer reporte aparece el día 1 del mes siguiente al lanzamiento del sitio."
      class="mt-8"
    />

    <div v-else class="mt-6 grid gap-6 lg:grid-cols-[14rem_1fr]">
      <!-- Meses ya generados -->
      <nav class="flex gap-2 overflow-x-auto lg:flex-col" aria-label="Meses">
        <button
          v-for="r in reports"
          :key="r.id"
          class="shrink-0 rounded-xl2 border px-4 py-2.5 text-left text-sm font-medium capitalize transition"
          :class="r.id === selectedId ? 'border-gold bg-gold-light text-gold' : 'border-line bg-white text-muted hover:text-gold'"
          @click="selectedId = r.id"
        >
          {{ monthName(r) }}
        </button>
      </nav>

      <!-- Reporte escrito -->
      <article v-if="report" class="card p-6 sm:p-8">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="text-2xl font-bold capitalize text-ink">{{ monthName(report) }}</h2>
            <p class="mt-1 text-xs text-muted">Generado el {{ generatedLabel }}</p>
          </div>
          <button class="btn-outline text-sm" @click="copyReport">{{ copied ? "¡Copiado!" : "Copiar texto" }}</button>
        </div>

        <section v-for="s in report.data.sections" :key="s.title" class="mt-6 border-t border-line pt-5">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-gold-dark">{{ s.title }}</h3>
          <div class="mt-2 grid gap-4 sm:grid-cols-[1fr_14rem] sm:items-end">
            <p class="text-ink">{{ s.text }}</p>
            <MiniBars v-if="chartFor(s.title)" v-bind="chartFor(s.title)!" />
          </div>
        </section>
      </article>
    </div>
  </div>
</template>
