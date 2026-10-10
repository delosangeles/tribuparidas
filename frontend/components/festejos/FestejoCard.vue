<script setup lang="ts">
import type { Festejo } from "~/types";

const props = defineProps<{ festejo: Festejo; admin?: boolean; compact?: boolean }>();
defineEmits<{ approve: [Festejo]; edit: [Festejo]; remove: [Festejo] }>();

const THEME: Record<Festejo["kind"], { icon: string; tint: string; label: string }> = {
  monthiversary: { icon: "heart", tint: "bg-rose-50 text-rose-500", label: "Mesversario" },
  child_birthday: { icon: "star", tint: "bg-amber-50 text-amber-500", label: "Cumpleaños" },
  mother_birthday: { icon: "flower", tint: "bg-gold-light text-gold", label: "Mamá cumpleañera" },
  manual: { icon: "users", tint: "bg-emerald-50 text-emerald-600", label: "Festejo" },
};

const theme = computed(() => THEME[props.festejo.kind]);

const dateLabel = computed(() => {
  const [y, m, d] = props.festejo.event_date.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" }).format(new Date(y, m - 1, d));
});

const subtitle = computed(() =>
  props.festejo.child_name ? `Mamá: ${props.festejo.mother_name}` : props.festejo.kind === "manual" ? props.festejo.mother_name : ""
);
</script>

<template>
  <article class="card flex flex-col overflow-hidden" :class="festejo.status === 'pending' && admin ? 'ring-1 ring-amber-300' : ''">
    <div class="flex items-center gap-4 p-4" :class="compact ? '' : 'sm:flex-col sm:py-6 sm:text-center'">
      <img
        v-if="festejo.photo"
        :src="festejo.photo"
        :alt="`Foto de ${festejo.child_name || festejo.mother_name}`"
        class="shrink-0 rounded-full object-cover"
        :class="compact ? 'h-10 w-10' : 'h-20 w-20'"
      />
      <span v-else class="flex shrink-0 items-center justify-center rounded-full" :class="[theme.tint, compact ? 'h-10 w-10' : 'h-14 w-14']">
        <AppIcon :name="theme.icon" :size="compact ? 20 : 28" />
      </span>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold uppercase tracking-wide text-muted">{{ theme.label }}</p>
        <p class="mt-0.5 font-semibold text-ink" :class="compact ? 'text-sm' : 'text-lg'">{{ festejo.headline }}</p>
        <p v-if="subtitle" class="text-sm text-muted">{{ subtitle }}</p>
        <p v-if="festejo.note" class="mt-1 text-sm text-muted">{{ festejo.note }}</p>
        <p class="mt-1 text-sm capitalize text-gold-dark">{{ dateLabel }}</p>
      </div>
    </div>

    <div v-if="admin" class="flex flex-wrap items-center gap-2 border-t border-line bg-vanilla/60 px-4 py-2">
      <span :class="festejo.status === 'approved' ? 'badge-approved' : 'badge-pending'">
        {{ festejo.status === "approved" ? "Aprobado" : "Pendiente" }}
      </span>
      <div class="ml-auto flex gap-1">
        <button v-if="festejo.status === 'pending'" class="btn-outline !px-2 !py-1 text-xs" @click="$emit('approve', festejo)">Aprobar</button>
        <button class="btn-outline !px-2 !py-1 text-xs" @click="$emit('edit', festejo)">Editar</button>
        <button class="btn-outline !px-2 !py-1 text-xs text-rose-500" @click="$emit('remove', festejo)">Eliminar</button>
      </div>
    </div>
  </article>
</template>
