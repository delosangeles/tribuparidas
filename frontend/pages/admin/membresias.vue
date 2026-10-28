<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { MembershipRow } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const rows = ref<MembershipRow[]>([]);
const page = ref(1);
const search = ref("");
const hasNext = ref(false);
const hasPrevious = ref(false);
const busy = ref<number | null>(null);

async function load() {
  const { data } = await portalService.adminMemberships({ page: page.value, search: search.value || undefined });
  rows.value = data.results;
  hasNext.value = Boolean(data.next);
  hasPrevious.value = Boolean(data.previous);
}
await load();

let timer: ReturnType<typeof setTimeout> | null = null;
watch(search, () => {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    page.value = 1;
    load();
  }, 300);
});
watch(page, load);

async function toggle(row: MembershipRow) {
  busy.value = row.id;
  try {
    Object.assign(row, (await portalService.adminSetMembership(row.id, !row.membership_active)).data);
  } finally {
    busy.value = null;
  }
}
</script>

<template>
  <div class="space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Membresías</h1>
      <p class="text-sm text-muted">
        Todas las cuentas aprobadas tienen la membresía activa por defecto. Suspéndela para que una usuaria no pueda usar su tarjeta ni canjear descuentos.
      </p>
    </header>
    <input v-model="search" type="search" class="input max-w-sm" placeholder="Buscar por nombre, correo o teléfono" aria-label="Buscar" />

    <div class="card overflow-x-auto">
      <table class="w-full min-w-[36rem] text-left text-sm">
        <thead class="border-b border-line text-xs uppercase tracking-wide text-muted">
          <tr><th class="p-3">Usuaria</th><th class="p-3">Cédula</th><th class="p-3">Membresía</th><th class="p-3" /></tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" class="border-b border-line last:border-0">
            <td class="p-3"><p class="font-medium text-ink">{{ row.first_name }} {{ row.last_name }}</p><p class="text-xs text-muted">{{ row.email }}</p></td>
            <td class="p-3 text-muted">{{ row.has_document ? "Registrada" : "Falta (sin tarjeta)" }}</td>
            <td class="p-3"><span :class="row.membership_active ? 'badge-approved' : 'badge-rejected'">{{ row.membership_active ? "Activa" : "Suspendida" }}</span></td>
            <td class="p-3 text-right">
              <button class="btn-outline !px-3 !py-1 text-xs" :disabled="busy === row.id" @click="toggle(row)">
                {{ row.membership_active ? "Suspender" : "Reactivar" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!rows.length" class="py-8 text-center text-sm text-muted">No se encontraron usuarias.</p>
    </div>
    <Pagination v-model:page="page" :has-next="hasNext" :has-previous="hasPrevious" />
  </div>
</template>
