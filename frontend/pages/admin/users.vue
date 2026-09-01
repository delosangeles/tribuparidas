<script setup lang="ts">
import { userService } from "~/services/user.service";
import type { User, UserRole } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const authStore = useAuthStore();

const ROLE_LABELS: Record<UserRole, string> = {
  user: "Usuario",
  admin: "Administrador",
  super_admin: "Super Admin",
};

const search = ref("");
const statusFilter = ref<"" | "pending" | "active">("");
const page = ref(1);
const loading = ref(false);
const users = ref<User[]>([]);
const pagination = ref<{ next: string | null; previous: string | null }>({ next: null, previous: null });

async function load() {
  loading.value = true;
  try {
    const { data } = await userService.adminList({
      search: search.value || undefined,
      is_active: statusFilter.value === "" ? undefined : statusFilter.value === "active",
      page: page.value,
    });
    users.value = data.results;
    pagination.value = { next: data.next, previous: data.previous };
  } finally {
    loading.value = false;
  }
}
await load();

watch([search, statusFilter], () => {
  page.value = 1;
  load();
});

function waLink(whatsapp: string) {
  return `https://wa.me/${whatsapp.replace(/\D/g, "")}`;
}

async function toggleActive(user: User) {
  const { data } = await userService.setActive(user.id, !user.is_active);
  user.is_active = data.is_active;
}

const roleActionLoading = ref<number | null>(null);
async function toggleRole(user: User) {
  roleActionLoading.value = user.id;
  try {
    const { data } = await userService.setRole(user.id, !user.is_staff);
    user.is_staff = data.is_staff;
    user.role = data.role;
  } finally {
    roleActionLoading.value = null;
  }
}

function changePage(next: number) {
  page.value = next;
  load();
}

const resetTarget = ref<User | null>(null);
const resetPassword = ref("");
const resetLoading = ref(false);
const copied = ref(false);

async function confirmResetPassword() {
  if (!resetTarget.value) return;
  resetLoading.value = true;
  try {
    const { data } = await userService.resetPassword(resetTarget.value.id);
    resetPassword.value = data.new_password;
  } finally {
    resetLoading.value = false;
  }
}

async function copyPassword() {
  await navigator.clipboard.writeText(resetPassword.value);
  copied.value = true;
}

function closeReset() {
  resetTarget.value = null;
  resetPassword.value = "";
  copied.value = false;
}

const showCreate = ref(false);
const createForm = reactive({ email: "", first_name: "", last_name: "", whatsapp: "", is_staff: false });
const createLoading = ref(false);
const createError = ref("");
const createdPassword = ref("");
const createdCopied = ref(false);

function openCreate() {
  createForm.email = "";
  createForm.first_name = "";
  createForm.last_name = "";
  createForm.whatsapp = "";
  createForm.is_staff = false;
  createError.value = "";
  createdPassword.value = "";
  createdCopied.value = false;
  showCreate.value = true;
}

async function submitCreate() {
  createLoading.value = true;
  createError.value = "";
  try {
    const { data } = await userService.adminCreate({ ...createForm });
    createdPassword.value = data.new_password;
    page.value = 1;
    await load();
  } catch (err) {
    createError.value = useErrorMessage(err);
  } finally {
    createLoading.value = false;
  }
}

async function copyCreatedPassword() {
  await navigator.clipboard.writeText(createdPassword.value);
  createdCopied.value = true;
}

function closeCreate() {
  showCreate.value = false;
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-ink">Usuarios</h1>
        <p class="mt-1 text-sm text-muted">Aprueba el acceso solo de quienes están en el grupo de WhatsApp de la tribu.</p>
      </div>
      <button v-if="authStore.isSuperAdmin" class="btn-primary" @click="openCreate">
        <AppIcon name="users" :size="16" /> Crear usuario
      </button>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2.5 sm:max-w-sm">
        <AppIcon name="search" :size="16" class="text-muted" />
        <input v-model="search" type="text" placeholder="Buscar por email o nombre..." class="w-full border-none bg-transparent text-sm outline-none" />
      </div>
      <div class="flex gap-2">
        <button class="btn-outline" :class="statusFilter === '' && '!border-gold !text-gold'" @click="statusFilter = ''">Todos</button>
        <button class="btn-outline" :class="statusFilter === 'pending' && '!border-gold !text-gold'" @click="statusFilter = 'pending'">Pendientes</button>
        <button class="btn-outline" :class="statusFilter === 'active' && '!border-gold !text-gold'" @click="statusFilter = 'active'">Activos</button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else class="mt-6 overflow-x-auto rounded-xl2 border border-line bg-white">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-line text-xs uppercase text-muted">
          <tr>
            <th class="px-4 py-3">Usuario</th>
            <th class="px-4 py-3">WhatsApp</th>
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
            <td class="px-4 py-3">
              <a v-if="user.whatsapp" :href="waLink(user.whatsapp)" target="_blank" class="inline-flex items-center gap-1 text-emerald-600 hover:underline">
                <AppIcon name="whatsapp" :size="14" />{{ user.whatsapp }}
              </a>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="px-4 py-3">
              <span class="text-muted">{{ ROLE_LABELS[user.role] }}</span>
              <span v-if="user.role === 'user' && user.is_entrepreneur" class="ml-1 text-xs text-muted">(emprendedora)</span>
            </td>
            <td class="px-4 py-3 text-muted">{{ user.businesses_count ?? 0 }}</td>
            <td class="px-4 py-3">
              <span :class="user.is_active ? 'badge-approved' : 'badge-rejected'">{{ user.is_active ? "Activo" : "Inactivo" }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-2">
                <button v-if="!user.is_staff" class="btn-outline !px-2 !py-1 text-xs" @click="toggleActive(user)">
                  {{ user.is_active ? "Desactivar" : "Activar" }}
                </button>
                <button v-if="!user.is_staff" class="btn-outline !px-2 !py-1 text-xs" @click="resetTarget = user">
                  Resetear contraseña
                </button>
                <button
                  v-if="authStore.isSuperAdmin && !user.is_superuser"
                  class="btn-outline !px-2 !py-1 text-xs"
                  :disabled="roleActionLoading === user.id"
                  @click="toggleRole(user)"
                >
                  {{ user.is_staff ? "Quitar Administrador" : "Ascender a Administrador" }}
                </button>
              </div>
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

    <Teleport to="body">
      <div v-if="resetTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <template v-if="resetPassword">
            <p class="text-lg font-semibold text-ink">Nueva contraseña generada</p>
            <p class="mt-1 text-sm text-muted">
              Cópiala y envíasela a {{ resetTarget.first_name }} por WhatsApp. No queda guardada en ningún otro lugar.
            </p>
            <div class="mt-4 flex items-center gap-2 rounded-xl2 border border-line bg-vanilla px-3 py-2">
              <code class="flex-1 break-all text-sm text-ink">{{ resetPassword }}</code>
              <button class="btn-outline shrink-0 !px-2 !py-1 text-xs" @click="copyPassword">
                {{ copied ? "¡Copiada!" : "Copiar" }}
              </button>
            </div>
            <a
              v-if="resetTarget.whatsapp"
              :href="waLink(resetTarget.whatsapp)"
              target="_blank"
              class="btn-primary mt-4 w-full"
            >
              <AppIcon name="whatsapp" :size="16" /> Abrir WhatsApp
            </a>
            <button class="btn-ghost mt-2 w-full" @click="closeReset">Cerrar</button>
          </template>
          <template v-else>
            <p class="text-lg font-semibold text-ink">¿Resetear la contraseña de {{ resetTarget.first_name }}?</p>
            <p class="mt-1 text-sm text-muted">Se genera una contraseña nueva al azar; la actual deja de servir.</p>
            <div class="mt-6 flex justify-end gap-2">
              <button class="btn-ghost" @click="closeReset">Cancelar</button>
              <button class="btn-primary" :disabled="resetLoading" @click="confirmResetPassword">
                {{ resetLoading ? "Generando..." : "Generar nueva contraseña" }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
        <div class="card w-full max-w-sm p-6">
          <template v-if="createdPassword">
            <p class="text-lg font-semibold text-ink">Usuario creado</p>
            <p class="mt-1 text-sm text-muted">Cópiale esta contraseña y envíasela por WhatsApp. No queda guardada en ningún otro lugar.</p>
            <div class="mt-4 flex items-center gap-2 rounded-xl2 border border-line bg-vanilla px-3 py-2">
              <code class="flex-1 break-all text-sm text-ink">{{ createdPassword }}</code>
              <button class="btn-outline shrink-0 !px-2 !py-1 text-xs" @click="copyCreatedPassword">
                {{ createdCopied ? "¡Copiada!" : "Copiar" }}
              </button>
            </div>
            <button class="btn-primary mt-4 w-full" @click="closeCreate">Listo</button>
          </template>
          <template v-else>
            <p class="text-lg font-semibold text-ink">Crear usuario</p>
            <form class="mt-4 space-y-3" @submit.prevent="submitCreate">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
                  <input v-model="createForm.first_name" type="text" required class="field" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
                  <input v-model="createForm.last_name" type="text" required class="field" />
                </div>
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-ink">Correo</label>
                <input v-model="createForm.email" type="email" required class="field" placeholder="tu@email.com" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-ink">WhatsApp</label>
                <input v-model="createForm.whatsapp" type="text" class="field" placeholder="+57 300 000 0000" />
              </div>
              <label class="flex items-center gap-2 text-sm text-ink">
                <input v-model="createForm.is_staff" type="checkbox" class="h-4 w-4 rounded border-line" />
                Crear como Administrador
              </label>
              <p v-if="createError" class="text-sm text-rose-500">{{ createError }}</p>
              <div class="flex justify-end gap-2 pt-2">
                <button type="button" class="btn-ghost" @click="closeCreate">Cancelar</button>
                <button type="submit" class="btn-primary" :disabled="createLoading">
                  {{ createLoading ? "Creando..." : "Crear usuario" }}
                </button>
              </div>
            </form>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>
