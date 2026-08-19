<script setup lang="ts">
import { businessService } from "~/services/business.service";
import { userService } from "~/services/user.service";
import type { Business } from "~/types";

definePageMeta({ layout: "admin", middleware: "admin" });

const { data } = await useAsyncData("admin-overview", async () => {
  const [approved, pending, rejected, users, recent] = await Promise.all([
    businessService.adminList({ status: "approved", page_size: 1 }),
    businessService.adminList({ status: "pending", page_size: 1 }),
    businessService.adminList({ status: "rejected", page_size: 1 }),
    userService.adminList({ page_size: 1 }),
    businessService.adminList({ page_size: 6, ordering: "-created_at" }),
  ]);
  return {
    approvedCount: approved.data.count,
    pendingCount: pending.data.count,
    rejectedCount: rejected.data.count,
    usersCount: users.data.count,
    recent: recent.data.results as Business[],
  };
});
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Panel de administración</h1>
    <p class="mt-1 text-sm text-muted">Estadísticas generales de la plataforma.</p>

    <div class="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Total emprendimientos" :value="(data?.approvedCount ?? 0) + (data?.pendingCount ?? 0) + (data?.rejectedCount ?? 0)" icon="briefcase" />
      <StatCard label="Aprobados" :value="data?.approvedCount ?? 0" icon="check-circle" />
      <StatCard label="Pendientes por revisar" :value="data?.pendingCount ?? 0" icon="clock" :trend-positive="false" />
      <StatCard label="Usuarios registrados" :value="data?.usersCount ?? 0" icon="users" />
    </div>

    <div class="mt-8 card p-5">
      <div class="flex items-center justify-between">
        <p class="font-semibold text-ink">Emprendimientos recientes</p>
        <NuxtLink to="/admin/businesses" class="text-sm font-semibold text-gold hover:underline">Ver todos</NuxtLink>
      </div>

      <div class="mt-4 divide-y divide-line">
        <div v-for="business in data?.recent" :key="business.id" class="flex items-center justify-between py-3">
          <div class="flex items-center gap-3">
            <span class="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-gold-light text-gold">
              <img v-if="business.logo" :src="business.logo" class="h-full w-full object-cover" />
              <AppIcon v-else name="briefcase" :size="16" />
            </span>
            <div>
              <p class="text-sm font-semibold text-ink">{{ business.name }}</p>
              <p class="text-xs text-muted">{{ business.category?.name }}</p>
            </div>
          </div>
          <StatusBadge :status="business.status" />
        </div>
        <p v-if="!data?.recent?.length" class="py-6 text-center text-sm text-muted">Todavía no hay emprendimientos registrados.</p>
      </div>
    </div>
  </div>
</template>
