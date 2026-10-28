<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalChange } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const changes = ref<PortalChange[]>([]);
usePortalBusiness(async (id) => {
  changes.value = (await portalService.changes(id)).data.results;
});

const ENTITY: Record<string, string> = {
  business: "Emprendimiento", benefit: "Beneficio", faq: "Pregunta frecuente", image: "Imagen", review_reply: "Respuesta a opinión",
};
const ACTION: Record<string, string> = { create: "creó", update: "editó", delete: "eliminó", reorder: "reordenó", review: "revisó" };
const show = (v: string | null) => (v === null || v === "" ? "—" : v);
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Historial de cambios</h1>
      <p class="text-sm text-muted">Quién cambió qué en tu emprendimiento y cuándo.</p>
    </header>
    <EmptyState v-if="!changes.length" icon="clock" title="Todavía no hay cambios registrados" />
    <ol class="space-y-3">
      <li v-for="c in changes" :key="c.id" class="card p-4">
        <p class="text-sm text-ink">
          <strong>{{ c.actor_name || "Alguien del equipo" }}</strong> {{ ACTION[c.action] ?? c.action }} · {{ ENTITY[c.entity] ?? c.entity }}
        </p>
        <p class="text-xs text-muted">{{ new Date(c.created_at).toLocaleString("es-CO") }}</p>
        <ul v-if="Object.keys(c.changes).length" class="mt-2 space-y-1 text-xs text-muted">
          <li v-for="(change, field) in c.changes" :key="field">
            <span class="font-medium text-ink">{{ field }}:</span> {{ show(change.from) }} → {{ show(change.to) }}
          </li>
        </ul>
      </li>
    </ol>
  </div>
</template>
