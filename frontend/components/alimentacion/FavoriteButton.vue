<script setup lang="ts">
import { alimentacionService } from "~/services/alimentacion.service";

const props = defineProps<{ slug: string; modelValue: boolean }>();
const emit = defineEmits<{ (e: "update:modelValue", value: boolean): void }>();

const authStore = useAuthStore();
const busy = ref(false);

async function toggle() {
  // Los favoritos son solo para usuarias con sesión.
  if (!authStore.isAuthenticated) {
    return navigateTo({ path: "/login", query: { redirect: useRoute().fullPath } });
  }
  if (busy.value) return;
  busy.value = true;
  const next = !props.modelValue;
  emit("update:modelValue", next); // optimista
  try {
    if (next) await alimentacionService.addFavorite(props.slug);
    else await alimentacionService.removeFavorite(props.slug);
  } catch {
    emit("update:modelValue", !next);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <button
    type="button"
    class="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-white/90 transition hover:border-gold"
    :class="modelValue ? 'text-rose-500' : 'text-muted'"
    :aria-pressed="modelValue"
    :aria-label="modelValue ? 'Quitar de favoritos' : 'Guardar en favoritos'"
    @click.prevent.stop="toggle"
  >
    <AppIcon :name="modelValue ? 'heart-filled' : 'heart'" :size="18" :class="modelValue ? 'fill-current' : ''" />
  </button>
</template>
