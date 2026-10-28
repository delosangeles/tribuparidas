<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalBenefit, PortalBusiness, PortalStats } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal" });

const stats = ref<PortalStats | null>(null);
const business = ref<PortalBusiness | null>(null);
const benefit = ref<PortalBenefit | null>(null);
const error = ref("");

const { portal } = usePortalBusiness(async (id) => {
  error.value = "";
  try {
    const [s, b] = await Promise.all([portalService.stats(id), portalService.business(id)]);
    stats.value = s.data;
    business.value = b.data;
    benefit.value = portal.isOwner ? (await portalService.benefit(id)).data : null;
  } catch (err) {
    error.value = useErrorMessage(err);
  }
});

const BENEFIT_STATUS: Record<string, string> = {
  pending: "Pendiente de aprobación",
  approved: "Aprobado y publicado",
  rejected: "Rechazado: ajústalo y vuelve a enviarlo",
};
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-ink">Hola{{ portal.current ? `, ${portal.current.name}` : "" }}</h1>
      <p class="text-sm text-muted">Aquí ves cómo le va a tu emprendimiento en la tribu.</p>
    </header>

    <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>

    <div v-if="stats" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatCard label="Visitas hoy" :value="stats.visits.today" icon="users" />
      <StatCard label="Visitas 7 días" :value="stats.visits.last_7_days" icon="chart" />
      <StatCard label="Visitas 30 días" :value="stats.visits.last_30_days" icon="chart" />
      <StatCard label="Descuentos aplicados" :value="stats.redemptions.total" icon="gift" :trend="`${stats.redemptions.today} hoy`" />
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <NuxtLink to="/portal/escanear" class="card flex items-center gap-4 p-5 transition hover:border-gold">
        <span class="flex h-12 w-12 items-center justify-center rounded-full bg-gold-light text-gold"><AppIcon name="camera" :size="24" /></span>
        <span>
          <span class="block font-semibold text-ink">Escanear tarjeta</span>
          <span class="text-sm text-muted">Valida el QR o el código de una usuaria y aplica su descuento.</span>
        </span>
      </NuxtLink>

      <div v-if="business" class="card p-5">
        <p class="font-semibold text-ink">Tu página pública</p>
        <NuxtLink :to="business.public_path" class="mt-1 block break-all text-sm text-gold hover:underline">{{ business.public_path }}</NuxtLink>
        <p class="mt-2 text-sm text-muted">Calificación: {{ business.average_rating }} / 5</p>
      </div>
    </div>

    <div v-if="portal.isOwner" class="card p-5">
      <p class="font-semibold text-ink">Beneficio Tribu</p>
      <template v-if="benefit">
        <p class="mt-1 text-sm text-ink">{{ benefit.percentage }}% de descuento</p>
        <p class="text-xs" :class="benefit.status === 'approved' ? 'text-emerald-600' : 'text-amber-600'">{{ BENEFIT_STATUS[benefit.status] }}</p>
      </template>
      <p v-else class="mt-1 text-sm text-muted">Aún no tienes un beneficio. Sin beneficio aprobado no se pueden aplicar descuentos.</p>
      <NuxtLink to="/portal/beneficio" class="btn-outline mt-3">{{ benefit ? "Editar beneficio" : "Crear beneficio" }}</NuxtLink>
    </div>
  </div>
</template>
