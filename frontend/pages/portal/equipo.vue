<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalTeamMember } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const team = ref<PortalTeamMember[]>([]);
const form = reactive({ email: "", days: "" });
const error = ref("");
const message = ref("");
const toRemove = ref<PortalTeamMember | null>(null);
const renewing = ref<number | null>(null);
const renewDays = ref("");

const { businessId } = usePortalBusiness(load);

async function load() {
  team.value = (await portalService.team(businessId.value)).data;
}

const toDays = (value: string) => (value.trim() ? Number(value) : null);

async function add() {
  error.value = message.value = "";
  try {
    await portalService.addSeller(businessId.value, { email: form.email.trim(), days: toDays(form.days) });
    message.value = "Vendedora agregada.";
    form.email = form.days = "";
    await load();
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

async function renew(member: PortalTeamMember) {
  error.value = message.value = "";
  try {
    await portalService.updateSeller(businessId.value, member.id, toDays(renewDays.value));
    renewing.value = null;
    renewDays.value = "";
    await load();
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

async function remove() {
  if (!toRemove.value) return;
  await portalService.removeSeller(businessId.value, toRemove.value.id);
  toRemove.value = null;
  await load();
}

function until(member: PortalTeamMember) {
  if (!member.expires_at) return "Sin vencimiento";
  const date = new Date(member.expires_at).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
  return member.is_expired ? `Venció el ${date}` : `Hasta el ${date}`;
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Mi equipo</h1>
      <p class="text-sm text-muted">
        Agrega vendedoras que ya estén registradas en la plataforma (con su correo). Ellas pueden escanear y canjear descuentos y ver
        las estadísticas, pero no editar tu emprendimiento. Si les pones una duración, su acceso se cierra solo al terminar.
      </p>
    </header>

    <form class="card grid gap-3 p-5 md:grid-cols-[1fr_9rem_auto]" @submit.prevent="add">
      <input v-model="form.email" type="email" required class="input" placeholder="Correo de la persona" aria-label="Correo de la persona" />
      <input v-model="form.days" type="number" min="1" max="365" class="input" placeholder="Días (opcional)" aria-label="Duración en días" />
      <button class="btn-primary" type="submit">Agregar</button>
      <p class="text-xs text-muted md:col-span-3">Deja los días vacíos para que no venza.</p>
      <p v-if="error" class="text-sm text-rose-600 md:col-span-3" role="alert">{{ error }}</p>
      <p v-if="message" class="text-sm text-emerald-600 md:col-span-3" role="status">{{ message }}</p>
    </form>

    <EmptyState v-if="!team.length" icon="users" title="Aún no tienes vendedoras" description="Agrega a la primera con su correo." />
    <ul v-else class="space-y-3">
      <li v-for="m in team" :key="m.id" class="card p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="font-medium text-ink">{{ m.user_name || m.user_email }}</p>
            <p class="text-xs text-muted">{{ m.user_email }}</p>
            <p class="mt-1 text-xs" :class="m.is_expired ? 'text-rose-600' : 'text-muted'">{{ until(m) }}</p>
          </div>
          <div class="flex gap-2">
            <button class="btn-outline !px-3 !py-1 text-xs" @click="renewing = renewing === m.id ? null : m.id">
              {{ m.is_expired ? "Renovar" : "Cambiar duración" }}
            </button>
            <button class="btn-outline !px-3 !py-1 text-xs !text-rose-500" @click="toRemove = m">Quitar</button>
          </div>
        </div>
        <form v-if="renewing === m.id" class="mt-3 flex gap-2" @submit.prevent="renew(m)">
          <input v-model="renewDays" type="number" min="1" max="365" class="input w-40" placeholder="Días (vacío = sin vencimiento)" aria-label="Nueva duración en días" />
          <button class="btn-primary !px-3 !py-1 text-xs" type="submit">Guardar</button>
        </form>
      </li>
    </ul>

    <ConfirmDialog
      :open="Boolean(toRemove)"
      title="¿Quitar de tu equipo?"
      description="Pierde el acceso a tu portal de inmediato. Puedes volver a agregarla cuando quieras."
      confirm-label="Quitar"
      danger
      @confirm="remove"
      @cancel="toRemove = null"
    />
  </div>
</template>
