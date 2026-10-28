<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalStats } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal" });

const stats = ref<PortalStats | null>(null);
usePortalBusiness(async (id) => {
  stats.value = (await portalService.stats(id)).data;
});

const PERIODS = [
  { key: "today", label: "Hoy" },
  { key: "last_7_days", label: "7 días" },
  { key: "last_30_days", label: "30 días" },
  { key: "total", label: "Total" },
] as const;
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-ink">Estadísticas</h1>
      <p class="text-sm text-muted">Personas que abrieron tu tarjeta y descuentos aplicados.</p>
    </header>
    <template v-if="stats">
      <section>
        <h2 class="mb-2 font-semibold text-ink">Visitas a tu tarjeta</h2>
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard v-for="p in PERIODS" :key="p.key" :label="p.label" :value="stats.visits[p.key]" icon="users" />
        </div>
      </section>
      <section>
        <h2 class="mb-2 font-semibold text-ink">Descuentos aplicados</h2>
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard v-for="p in PERIODS" :key="p.key" :label="p.label" :value="stats.redemptions[p.key]" icon="gift" />
        </div>
      </section>
    </template>
  </div>
</template>
