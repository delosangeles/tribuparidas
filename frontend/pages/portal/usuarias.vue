<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalMember } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const members = ref<PortalMember[]>([]);
const count = ref(0);
const page = ref(1);
const search = ref("");
const hasNext = ref(false);
const hasPrevious = ref(false);

const { businessId } = usePortalBusiness(() => {
  page.value = 1;
  return load();
});

async function load() {
  const { data } = await portalService.members(businessId.value, { page: page.value, search: search.value || undefined });
  members.value = data.results;
  count.value = data.count;
  hasNext.value = Boolean(data.next);
  hasPrevious.value = Boolean(data.previous);
}

let timer: ReturnType<typeof setTimeout> | null = null;
watch(search, () => {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    page.value = 1;
    load();
  }, 300);
});
watch(page, load);

const fullName = (m: PortalMember) => `${m.first_name} ${m.last_name}`.trim() || m.email;
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Usuarias</h1>
      <p class="text-sm text-muted">
        Usuarias que abrieron tu tarjeta o usaron un descuento y aceptaron compartir sus datos contigo. Solo consulta:
        trátalas con respeto y no las compartas (Ley 1581 de 2012).
      </p>
    </header>

    <input v-model="search" type="search" class="input max-w-sm" placeholder="Buscar por nombre, correo o teléfono" aria-label="Buscar usuarias" />
    <p class="text-xs text-muted">{{ count }} usuarias</p>

    <EmptyState v-if="!members.length" icon="users" title="Todavía no hay usuarias" description="Aparecerán cuando abran tu tarjeta o canjeen un descuento." />
    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[34rem] text-left text-sm">
        <thead class="border-b border-line text-xs uppercase tracking-wide text-muted">
          <tr><th class="p-3">Nombre</th><th class="p-3">Teléfono</th><th class="p-3">Correo</th><th class="p-3 text-right">Descuentos</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in members" :key="m.id" class="border-b border-line last:border-0">
            <td class="p-3 font-medium text-ink">{{ fullName(m) }}</td>
            <td class="p-3 text-muted">{{ m.whatsapp || "—" }}</td>
            <td class="p-3 text-muted">{{ m.email }}</td>
            <td class="p-3 text-right text-ink">{{ m.redemption_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <Pagination v-model:page="page" :has-next="hasNext" :has-previous="hasPrevious" />
  </div>
</template>
