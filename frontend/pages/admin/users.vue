<script setup lang="ts">
import { userService } from "~/services/user.service";
import type { User } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const search = ref("");
const page = ref(1);
const loading = ref(false);
const users = ref<User[]>([]);
const pagination = ref<{ next: string | null; previous: string | null }>({ next: null, previous: null });

async function load() {
  loading.value = true;
  try {
    const { data } = await userService.adminList({ search: search.value || undefined, page: page.value });
    users.value = data.results;
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

async function toggleActive(user: User) {
  const { data } = await userService.setActive(user.id, !user.is_active);
  user.is_active = data.is_active;
}

function changePage(next: number) {
  page.value = next;
  load();
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Usuarios</h1>
    <p class="mt-1 text-sm text-muted">Administra el acceso de las personas registradas.</p>

    <div class="mt-4 flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 sm:max-w-sm">
      <AppIcon name="search" :size="16" class="text-muted" />
      <input v-model="search" type="text" placeholder="Buscar por email o nombre..." class="w-full border-none bg-transparent text-sm outline-none" />
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Usuario</th>
            <th class="px-4 py-3">Rol</th>
            <th class="px-4 py-3">Emprendimientos</th>
            <th class="px-4 py-3">Estado</th>
            <th class="px-4 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-line">
          <tr v-for="user in users" :key="user.id">
            <td class="px-4 py-3">
              <p class="font-medium text-ink">{{ user.first_name }} {{ user.last_name }}</p>
              <p class="text-xs text-muted">{{ user.email }}</p>
            </td>
            <td class="px-4 py-3 text-muted">{{ user.is_staff ? "Admin" : user.is_entrepreneur ? "Emprendedor" : "Visitante" }}</td>
            <td class="px-4 py-3 text-muted">{{ user.businesses_count ?? 0 }}</td>
            <td class="px-4 py-3">
              <span :class="user.is_active ? 'badge-approved' : 'badge-rejected'">{{ user.is_active ? "Activo" : "Inactivo" }}</span>
            </td>
            <td class="px-4 py-3">
              <button v-if="!user.is_staff" class="btn-outline !px-2 !py-1 text-xs" @click="toggleActive(user)">
                {{ user.is_active ? "Desactivar" : "Activar" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!users.length" class="py-8 text-center text-sm text-muted">No se encontraron usuarios.</p>
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
