<script setup lang="ts">
import { businessService } from "~/services/business.service";
import { portalService } from "~/services/portal.service";
import { userService } from "~/services/user.service";
import type { AdminBenefit, Business, BusinessOwnerRow, User } from "~/types";

// Solo el equipo admin (is_staff) asigna dueñas/vendedoras y aprueba beneficios.
definePageMeta({ layout: "admin", middleware: "admin" });

const tab = ref<"owners" | "benefits">("owners");
const owners = ref<BusinessOwnerRow[]>([]);
const benefits = ref<AdminBenefit[]>([]);
const error = ref("");

async function loadOwners() {
  owners.value = (await portalService.adminOwners({ page_size: 100 })).data.results;
}
async function loadBenefits() {
  benefits.value = (await portalService.adminBenefits({ page_size: 100, ordering: "-updated_at" })).data.results;
}
await Promise.all([loadOwners(), loadBenefits()]);

// ---- asignar
const userSearch = ref("");
const businessSearch = ref("");
const userResults = ref<User[]>([]);
const businessResults = ref<Business[]>([]);
const picked = reactive<{ user: User | null; business: Business | null; role: "owner" | "seller" }>({ user: null, business: null, role: "owner" });

let userTimer: ReturnType<typeof setTimeout> | null = null;
watch(userSearch, (value) => {
  if (userTimer) clearTimeout(userTimer);
  if (value.trim().length < 2) return (userResults.value = []);
  userTimer = setTimeout(async () => {
    userResults.value = (await userService.adminList({ search: value.trim(), is_approved: true, page_size: 8 })).data.results;
  }, 300);
});
let bizTimer: ReturnType<typeof setTimeout> | null = null;
watch(businessSearch, (value) => {
  if (bizTimer) clearTimeout(bizTimer);
  if (value.trim().length < 2) return (businessResults.value = []);
  bizTimer = setTimeout(async () => {
    businessResults.value = (await businessService.adminList({ search: value.trim(), status: "approved", page_size: 8 })).data.results;
  }, 300);
});

async function assign() {
  if (!picked.user || !picked.business) return;
  error.value = "";
  try {
    await portalService.adminAssign({ user: picked.user.id, business: picked.business.id, role: picked.role });
    picked.user = picked.business = null;
    userSearch.value = businessSearch.value = "";
    userResults.value = businessResults.value = [];
    await loadOwners();
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

async function remove(row: BusinessOwnerRow) {
  await portalService.adminRemove(row.id);
  await loadOwners();
}
async function toggleRole(row: BusinessOwnerRow) {
  await portalService.adminSetRole(row.id, row.role === "owner" ? "seller" : "owner");
  await loadOwners();
}

// ---- beneficios
const BENEFIT_BADGE: Record<string, string> = { pending: "badge-pending", approved: "badge-approved", rejected: "badge-rejected" };
const BENEFIT_LABEL: Record<string, string> = { pending: "Pendiente", approved: "Aprobado", rejected: "Rechazado" };
async function review(benefit: AdminBenefit, approve: boolean) {
  const { data } = approve ? await portalService.adminApproveBenefit(benefit.id) : await portalService.adminRejectBenefit(benefit.id);
  Object.assign(benefit, data);
}
const pendingCount = computed(() => benefits.value.filter((b) => b.status === "pending").length);
const fullName = (u: User) => `${u.first_name} ${u.last_name}`.trim() || u.email;
</script>

<template>
  <div class="space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Portal de emprendimientos</h1>
      <p class="text-sm text-muted">Asigna dueñas y vendedoras a sus emprendimientos y aprueba los beneficios antes de publicarse.</p>
    </header>

    <div class="flex gap-2">
      <button class="btn-outline" :class="tab === 'owners' && '!border-gold !text-gold'" @click="tab = 'owners'">Accesos</button>
      <button class="btn-outline" :class="tab === 'benefits' && '!border-gold !text-gold'" @click="tab = 'benefits'">
        Beneficios <span v-if="pendingCount" class="rounded-full bg-gold px-2 text-xs text-white">{{ pendingCount }}</span>
      </button>
    </div>

    <template v-if="tab === 'owners'">
      <form class="card grid gap-3 p-5 md:grid-cols-4" @submit.prevent="assign">
        <div class="relative">
          <input v-model="userSearch" class="field" placeholder="Buscar persona (activa)" aria-label="Buscar persona" />
          <p v-if="picked.user" class="mt-1 text-xs text-emerald-600">✓ {{ fullName(picked.user) }}</p>
          <ul v-if="userResults.length" class="absolute z-10 mt-1 w-full rounded-xl2 border border-line bg-white p-1 shadow-soft">
            <li v-for="u in userResults" :key="u.id">
              <button type="button" class="w-full rounded-xl2 px-3 py-2 text-left text-sm hover:bg-gold-light" @click="picked.user = u; userResults = []">
                {{ fullName(u) }} <span class="text-xs text-muted">{{ u.email }}</span>
              </button>
            </li>
          </ul>
        </div>
        <div class="relative">
          <input v-model="businessSearch" class="field" placeholder="Buscar emprendimiento aprobado" aria-label="Buscar emprendimiento" />
          <p v-if="picked.business" class="mt-1 text-xs text-emerald-600">✓ {{ picked.business.name }}</p>
          <ul v-if="businessResults.length" class="absolute z-10 mt-1 w-full rounded-xl2 border border-line bg-white p-1 shadow-soft">
            <li v-for="b in businessResults" :key="b.id">
              <button type="button" class="w-full rounded-xl2 px-3 py-2 text-left text-sm hover:bg-gold-light" @click="picked.business = b; businessResults = []">{{ b.name }}</button>
            </li>
          </ul>
        </div>
        <select v-model="picked.role" class="field" aria-label="Rol">
          <option value="owner">Dueña (gestiona todo)</option>
          <option value="seller">Vendedora (escanea y ve estadísticas)</option>
        </select>
        <button class="btn-primary" :disabled="!picked.user || !picked.business">Asignar</button>
        <p v-if="error" class="text-sm text-rose-500 md:col-span-4">{{ error }}</p>
      </form>

      <div class="card overflow-x-auto">
        <table class="w-full min-w-[40rem] text-left text-sm">
          <thead class="border-b border-line text-xs uppercase tracking-wide text-muted">
            <tr><th class="p-3">Persona</th><th class="p-3">Emprendimiento</th><th class="p-3">Rol</th><th class="p-3">Cuenta</th><th class="p-3" /></tr>
          </thead>
          <tbody>
            <tr v-for="row in owners" :key="row.id" class="border-b border-line last:border-0">
              <td class="p-3"><p class="font-medium text-ink">{{ row.user_name }}</p><p class="text-xs text-muted">{{ row.user_email }}</p></td>
              <td class="p-3 text-ink">{{ row.business_name }}</td>
              <td class="p-3 text-muted">{{ row.role === "owner" ? "Dueña" : "Vendedora" }}</td>
              <td class="p-3 text-muted">{{ row.account_type === "portal" ? "Solo portal" : "Usuaria de la página" }}</td>
              <td class="space-x-1 p-3 text-right">
                <button class="btn-outline !px-2 !py-1 text-xs" @click="toggleRole(row)">Cambiar rol</button>
                <button class="btn-outline !px-2 !py-1 text-xs !text-rose-500" @click="remove(row)">Quitar</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!owners.length" class="py-8 text-center text-sm text-muted">Aún no hay accesos asignados.</p>
      </div>
    </template>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[40rem] text-left text-sm">
        <thead class="border-b border-line text-xs uppercase tracking-wide text-muted">
          <tr><th class="p-3">Emprendimiento</th><th class="p-3">Descuento</th><th class="p-3">Vigencia</th><th class="p-3">Estado</th><th class="p-3" /></tr>
        </thead>
        <tbody>
          <tr v-for="b in benefits" :key="b.id" class="border-b border-line last:border-0 align-top">
            <td class="p-3 font-medium text-ink">{{ b.business_name }}</td>
            <td class="p-3"><p class="text-ink">{{ b.percentage }}%</p><p class="max-w-xs text-xs text-muted">{{ b.conditions }}</p></td>
            <td class="p-3 text-xs text-muted">{{ b.valid_from || "—" }} → {{ b.valid_until || "sin fin" }}</td>
            <td class="p-3"><span :class="BENEFIT_BADGE[b.status]">{{ BENEFIT_LABEL[b.status] }}</span></td>
            <td class="space-x-1 p-3 text-right">
              <button v-if="b.status !== 'approved'" class="btn-primary !px-3 !py-1 text-xs" @click="review(b, true)">Aprobar</button>
              <button v-if="b.status === 'pending'" class="btn-outline !px-3 !py-1 text-xs !text-rose-500" @click="review(b, false)">Rechazar</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!benefits.length" class="py-8 text-center text-sm text-muted">Todavía no hay beneficios enviados.</p>
    </div>
  </div>
</template>
