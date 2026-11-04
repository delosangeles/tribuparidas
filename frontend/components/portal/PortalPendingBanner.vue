<script setup lang="ts">
import { siteSettingsService } from "~/services/site-settings.service";
import { reviewWhatsappUrl } from "~/utils/whatsapp";

// Aviso fijo mientras el emprendimiento está en espera de aprobación (1 a 2 días hábiles).
const portal = usePortalStore();
const authStore = useAuthStore();
const pending = computed(() => portal.current?.status === "pending");
const number = ref("");

watch(
  pending,
  async (isPending) => {
    if (!isPending || number.value) return;
    try {
      number.value = (await siteSettingsService.get()).data.access_whatsapp;
    } catch {
      // sin número: solo se muestra el aviso
    }
  },
  { immediate: true }
);

const url = computed(() =>
  reviewWhatsappUrl(number.value, portal.current?.name ?? "", authStore.user ? `${authStore.user.first_name} ${authStore.user.last_name}` : "", authStore.user?.email ?? "")
);
</script>

<template>
  <div v-if="pending" class="mb-5 rounded-xl2 border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900" role="status">
    <p class="font-semibold">Tu emprendimiento está en espera de aprobación</p>
    <p class="mt-1">
      Lo revisamos en 1 o 2 días hábiles. Mientras tanto puedes completar su información; aún no se ve en el directorio ni se pueden aplicar descuentos.
    </p>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="btn-outline mt-3 inline-flex">
      <AppIcon name="whatsapp" :size="16" /> Escribir al equipo por WhatsApp
    </a>
  </div>
</template>
