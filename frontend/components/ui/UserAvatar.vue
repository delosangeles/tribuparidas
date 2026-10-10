<script setup lang="ts">
// Foto de perfil o, si no hay, la inicial del nombre.
const props = withDefaults(
  defineProps<{ src?: string | null; name?: string | null; size?: "sm" | "md" | "lg" | "xl" }>(),
  { src: null, name: "", size: "md" }
);

const SIZES = { sm: "h-7 w-7 text-xs", md: "h-9 w-9 text-sm", lg: "h-14 w-14 text-xl", xl: "h-28 w-28 text-4xl" };
const initial = computed(() => (props.name || "?").trim().charAt(0).toUpperCase() || "?");
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="name ? `Foto de ${name}` : 'Foto de perfil'"
    class="shrink-0 rounded-full object-cover"
    :class="SIZES[size]"
  />
  <span
    v-else
    class="flex shrink-0 items-center justify-center rounded-full bg-gold-light font-semibold text-gold"
    :class="SIZES[size]"
    aria-hidden="true"
  >
    {{ initial }}
  </span>
</template>
