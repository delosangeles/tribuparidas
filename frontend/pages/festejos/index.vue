<script setup lang="ts">
import { festejosService } from "~/services/festejos.service";
import type { Festejo } from "~/types";

const authStore = useAuthStore();
const featureFlagStore = useFeatureFlagStore();
const isAdmin = computed(() => authStore.isAdmin);

// Antes de la fecha de lanzamiento (/admin/lanzamiento) solo entra el equipo admin.
if (!isAdmin.value && !featureFlagStore.isFestejosLive) {
  await navigateTo("/");
}

// Página solo de lectura: aprobar, editar, eliminar y agregar festejos se hace en /admin/festejos.
type Tab = "children" | "mothers";
const tab = ref<Tab>("children");

function toIso(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function parseIso(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
const today = toIso(new Date());

const week = ref<{ start: string; end: string; items: Festejo[] }>({ start: "", end: "", items: [] });
const month = ref<{ start: string; items: Festejo[] }>({ start: "", items: [] });
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [w, m] = await Promise.all([
      festejosService.list({ scope: "week", date: today, approved: true }),
      festejosService.list({ scope: "month", date: today, approved: true }),
    ]);
    week.value = { start: w.data.start, end: w.data.end, items: w.data.results };
    month.value = { start: m.data.start, items: m.data.results };
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}
await load();

const childrenItems = computed(() => week.value.items.filter((f) => f.kind !== "mother_birthday"));
const mothersItems = computed(() => week.value.items.filter((f) => f.kind === "mother_birthday"));
const shown = computed(() => (tab.value === "children" ? childrenItems.value : mothersItems.value));

// Cumpleaños del mes: cumpleaños de hijos y de mamás (los mesversarios van en la semana).
const monthBirthdays = computed(() => month.value.items.filter((f) => f.kind !== "monthiversary"));

function fmt(iso: string, opts: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat("es-CO", opts).format(parseIso(iso));
}
const weekLabel = computed(() =>
  week.value.start
    ? `Del lunes ${fmt(week.value.start, { day: "numeric", month: "long" })} al domingo ${fmt(week.value.end, { day: "numeric", month: "long" })}`
    : ""
);
const monthLabel = computed(() => (month.value.start ? fmt(month.value.start, { month: "long", year: "numeric" }) : ""));
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink">Festejos de la tribu</h1>
        <p class="mt-1 text-sm text-muted">Mesversarios y cumpleaños de la semana. De lunes a domingo.</p>
      </div>
      <NuxtLink v-if="isAdmin" to="/admin/festejos" class="btn-outline">
        <AppIcon name="settings" :size="16" /> Administrar festejos
      </NuxtLink>
    </div>

    <p class="mt-6 text-sm font-semibold capitalize text-gold-dark">{{ weekLabel }}</p>

    <!-- Tabs -->
    <div class="mt-3 flex gap-2 border-b border-line">
      <button
        class="-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'children' ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = 'children'"
      >
        Mesversarios y cumpleaños ({{ childrenItems.length }})
      </button>
      <button
        class="-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition"
        :class="tab === 'mothers' ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-gold'"
        @click="tab = 'mothers'"
      >
        Mamás cumpleañeras ({{ mothersItems.length }})
      </button>
    </div>

    <p v-if="error" class="mt-4 text-sm text-rose-500">{{ error }}</p>
    <LoadingSpinner v-if="loading" />
    <template v-else>
      <div v-if="shown.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <FestejoCard v-for="f in shown" :key="f.id" :festejo="f" />
      </div>
      <EmptyState
        v-else
        icon="heart"
        :title="tab === 'children' ? 'Esta semana no hay mesversarios ni cumpleaños' : 'Esta semana no hay mamás cumpleañeras'"
        description="Vuelve la próxima semana."
        class="mt-6"
      />

      <!-- Cumpleaños del mes -->
      <section class="mt-12">
        <h2 class="text-xl font-bold capitalize text-ink">Cumpleaños de {{ monthLabel }}</h2>
        <p class="mt-1 text-sm text-muted">Todos los cumpleaños del mes, de las mamás y de sus hijos.</p>
        <div v-if="monthBirthdays.length" class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <FestejoCard v-for="f in monthBirthdays" :key="`m-${f.id}`" :festejo="f" compact />
        </div>
        <p v-else class="mt-4 text-sm text-muted">No hay cumpleaños registrados este mes.</p>
      </section>
    </template>
  </div>
</template>
