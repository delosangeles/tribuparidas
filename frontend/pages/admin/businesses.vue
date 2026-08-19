<script setup lang="ts">
import { businessService } from "~/services/business.service";
import type { Business, BusinessStatus } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const statusFilter = ref<BusinessStatus | "">("");
const page = ref(1);
const loading = ref(false);
const businesses = ref<Business[]>([]);
const pagination = ref<{ next: string | null; previous: string | null }>({ next: null, previous: null });
const actingId = ref<number | null>(null);

async function load() {
  loading.value = true;
  try {
    const { data } = await businessService.adminList({
      status: statusFilter.value || undefined,
      page: page.value,
      ordering: "-created_at",
    });
    businesses.value = data.results;
    pagination.value = { next: data.next, previous: data.previous };
  } finally {
    loading.value = false;
  }
}
await load();

watch(statusFilter, () => {
  page.value = 1;
  load();
});

async function approve(business: Business) {
  actingId.value = business.id;
  try {
    await businessService.approve(business.id);
    business.status = "approved";
  } finally {
    actingId.value = null;
  }
}

async function reject(business: Business) {
  actingId.value = business.id;
  try {
    await businessService.reject(business.id);
    business.status = "rejected";
  } finally {
    actingId.value = null;
  }
}

function changePage(next: number) {
  page.value = next;
  load();
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Emprendimientos</h1>
    <p class="mt-1 text-sm text-muted">Aprueba, rechaza o revisa los emprendimientos publicados.</p>

    <div class="mt-4 flex gap-2">
      <button class="btn-outline" :class="statusFilter === '' && '!border-gold !text-gold'" @click="statusFilter = ''">Todos</button>
      <button class="btn-outline" :class="statusFilter === 'pending' && '!border-gold !text-gold'" @click="statusFilter = 'pending'">Pendientes</button>
      <button class="btn-outline" :class="statusFilter === 'approved' && '!border-gold !text-gold'" @click="statusFilter = 'approved'">Aprobados</button>
      <button class="btn-outline" :class="statusFilter === 'rejected' && '!border-gold !text-gold'" @click="statusFilter = 'rejected'">Rechazados</button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Emprendimiento</th>
            <th class="px-4 py-3">Dueño</th>
            <th class="px-4 py-3">Ciudad</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="business in businesses" :key="business.id">
            <td class="px-4 py-3 font-medium text-ink">{{ business.name }}</td>
            <td class="px-4 py-3 text-muted">{{ business.category?.name }}</td>
            <td class="px-4 py-3 text-muted">{{ business.city }}</td>
            <td class="px-4 py-3"><StatusBadge :status="business.status" /></td>
            <td class="px-4 py-3">
              <div class="flex gap-2">
                <NuxtLink :to="`/businesses/${business.slug}`" target="_blank" class="btn-ghost !px-2 !py-1">Ver</NuxtLink>
                <button
                  v-if="business.status !== 'approved'"
                  class="btn-outline !px-2 !py-1 text-xs !text-emerald-600"
                  :disabled="actingId === business.id"
                  @click="approve(business)"
                >
                  Aprobar
                </button>
                <button
                  v-if="business.status !== 'rejected'"
                  class="btn-outline !px-2 !py-1 text-xs !text-rose-500"
                  :disabled="actingId === business.id"
                  @click="reject(business)"
                >
                  Rechazar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!businesses.length" class="py-8 text-center text-sm text-muted">No hay emprendimientos con este filtro.</p>
    </div>

    <Pagination
      v-if="pagination.next || pagination.previous"
      :page="page"
      :has-next="Boolean(pagination.next)"
      :has-previous="Boolean(pagination.previous)"
      class="mt-4"
      @update:page="changePage"
    />
  </div>
</template>
