<script setup lang="ts">
// Barra de pestañas del perfil / registro. Las opcionales se marcan para que
// quede claro que no hay que llenarlas.
interface ProfileTab {
  key: string;
  label: string;
  optional?: boolean;
}

defineProps<{ tabs: ProfileTab[] }>();
const active = defineModel<string>({ required: true });
</script>

<template>
  <div role="tablist" class="flex gap-1 overflow-x-auto border-b border-line">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      role="tab"
      :aria-selected="active === tab.key"
      class="shrink-0 whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition"
      :class="active === tab.key ? 'border-gold text-gold' : 'border-transparent text-muted hover:text-ink'"
      @click="active = tab.key"
    >
      {{ tab.label }}
      <span v-if="tab.optional" class="ml-1 text-xs font-normal text-muted">(opcional)</span>
    </button>
  </div>
</template>
