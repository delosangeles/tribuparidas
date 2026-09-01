<script setup lang="ts">
import { activityLogService } from "~/services/activity-log.service";
import type { ActivityLogEntry } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const ACTION_LABELS: Record<string, string> = {
  business_approved: "Emprendimiento aprobado",
  business_rejected: "Emprendimiento rechazado",
  business_created_by_admin: "Emprendimiento creado (admin)",
  business_updated_by_admin: "Emprendimiento editado (admin)",
  user_created_by_admin: "Usuario creado (admin)",
  user_activated: "Usuario activado",
  user_deactivated: "Usuario desactivado",
  user_password_reset: "Contraseña reseteada",
  user_promoted_admin: "Ascendido a Administrador",
  user_demoted_admin: "Se quitó rol de Administrador",
  category_created: "Categoría creada",
  category_updated: "Categoría editada",
  category_deleted: "Categoría eliminada",
};

const search = ref("");
const page = ref(1);
const loading = ref(false);
const entries = ref<ActivityLogEntry[]>([]);
const pagination = ref<{ next: string | null; previous: string | null }>({ next: null, previous: null });

async function load() {
  loading.value = true;
  try {
    const { data } = await activityLogService.list({ search: search.value || undefined, page: page.value });
    entries.value = data.results;
    pagination.value = { next: data.next, previous: data.previous };
  } finally {
    loading.value = false;
  }
}
await load();

watch(search, () => {
  page.value = 1;
  load();
});

function changePage(next: number) {
  page.value = next;
  load();
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Historial de cambios</h1>
    <p class="mt-1 text-sm text-muted">Registro de acciones de moderación del equipo admin.</p>

    <div class="mt-4 flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 sm:max-w-sm">
      <AppIcon name="search" :size="16" class="text-muted" />
      <input v-model="search" type="text" placeholder="Buscar en la descripción..." class="w-full border-none bg-transparent text-sm outline-none" />
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Fecha</th>
            <th class="px-4 py-3">Quién</th>
            <th class="px-4 py-3">Acción</th>
            <th class="px-4 py-3">Detalle</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="entry in entries" :key="entry.id">
            <td class="px-4 py-3 whitespace-nowrap text-muted">{{ formatDate(entry.created_at) }}</td>
            <td class="px-4 py-3 text-ink">{{ entry.actor_name || entry.actor_email || "—" }}</td>
            <td class="px-4 py-3">
              <span class="badge bg-gold-light text-gold-dark">{{ ACTION_LABELS[entry.action] || entry.action }}</span>
            </td>
            <td class="px-4 py-3 text-muted">{{ entry.description }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!entries.length" class="py-8 text-center text-sm text-muted">Todavía no hay acciones registradas.</p>
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
