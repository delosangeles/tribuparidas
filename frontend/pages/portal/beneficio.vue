<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { PortalBenefit, PortalBusiness } from "~/types";
import { BENEFIT_TYPE_LABELS, suggestPortalBenefit } from "~/utils/benefit";

definePageMeta({ layout: "portal", middleware: "portal", ownerOnly: true });

const benefit = ref<PortalBenefit | null>(null);
// Beneficio que el emprendimiento ya tenía registrado en su perfil (antes del portal).
const registered = ref<{ label: string; detail: string } | null>(null);
const form = reactive({ percentage: 10, conditions: "", valid_from: "", valid_until: "" });
const saving = ref(false);
const message = ref("");
const error = ref("");

const STATUS: Record<string, { label: string; cls: string }> = {
  pending: { label: "Pendiente de aprobación", cls: "badge-pending" },
  approved: { label: "Aprobado y publicado", cls: "badge-approved" },
  rejected: { label: "Rechazado", cls: "badge-rejected" },
};

const { businessId } = usePortalBusiness(async (id) => {
  registered.value = null;
  benefit.value = (await portalService.benefit(id)).data;
  if (!benefit.value) {
    const business: PortalBusiness = (await portalService.business(id)).data;
    if (business.tribe_benefit && business.benefit_detail) {
      registered.value = { label: BENEFIT_TYPE_LABELS[business.benefit_type || ""] || "Beneficio Tribu", detail: business.benefit_detail };
      const suggestion = suggestPortalBenefit(business.benefit_detail);
      Object.assign(form, { percentage: suggestion.percentage ?? form.percentage, conditions: suggestion.conditions });
    }
  }
  if (benefit.value) {
    Object.assign(form, {
      percentage: benefit.value.percentage,
      conditions: benefit.value.conditions,
      valid_from: benefit.value.valid_from ?? "",
      valid_until: benefit.value.valid_until ?? "",
    });
  }
});

const percentageError = computed(() =>
  Number.isInteger(form.percentage) && form.percentage >= 1 && form.percentage <= 100 ? "" : "El porcentaje debe estar entre 1 y 100."
);

async function save() {
  if (percentageError.value) return;
  saving.value = true;
  message.value = error.value = "";
  try {
    const { data } = await portalService.saveBenefit(businessId.value, {
      percentage: form.percentage,
      conditions: form.conditions,
      valid_from: form.valid_from || null,
      valid_until: form.valid_until || null,
    });
    benefit.value = data;
    message.value = data.status === "pending" ? "Enviado. Un administrador lo revisará antes de publicarlo." : "Sin cambios.";
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Beneficio Tribu</h1>
      <p class="text-sm text-muted">El descuento que ofreces a las usuarias de la tribu. Cada cambio lo revisa un administrador antes de publicarse.</p>
    </header>

    <p v-if="benefit" :class="STATUS[benefit.status].cls" class="w-fit">{{ STATUS[benefit.status].label }}</p>

    <div v-if="registered && !benefit" class="card border-gold/40 bg-gold-light/40 p-4 text-sm text-ink" role="status">
      <p class="font-semibold">Tu emprendimiento ya tiene un beneficio registrado</p>
      <p class="mt-1"><strong>{{ registered.label }}:</strong> {{ registered.detail }}</p>
      <p class="mt-2 text-xs text-muted">
        Lo dejamos como punto de partida. Confirma el porcentaje y envíalo a revisión: cuando un administrador lo apruebe aparecerá con su % en tu
        tarjeta y en la tarjeta de las usuarias, y podrás aplicarlo escaneando su QR.
      </p>
    </div>

    <form class="card space-y-4 p-5" @submit.prevent="save">
      <label class="block">
        <span class="text-sm font-medium text-ink">Descuento (%)</span>
        <input v-model.number="form.percentage" type="number" min="1" max="100" step="1" required class="field mt-1 max-w-[8rem]" />
        <span v-if="percentageError" class="mt-1 block text-xs text-rose-500">{{ percentageError }}</span>
      </label>
      <label class="block">
        <span class="text-sm font-medium text-ink">Condiciones</span>
        <textarea v-model="form.conditions" rows="3" class="field mt-1" placeholder="Ej. Válido presentando tu tarjeta, una vez al día." />
      </label>
      <div class="grid gap-4 sm:grid-cols-2">
        <label><span class="text-sm font-medium text-ink">Vigente desde (opcional)</span><input v-model="form.valid_from" type="date" class="field mt-1" /></label>
        <label><span class="text-sm font-medium text-ink">Vigente hasta (opcional)</span><input v-model="form.valid_until" type="date" class="field mt-1" /></label>
      </div>
      <p class="text-xs text-muted">Cada usuaria puede usar el descuento una vez al día en tu emprendimiento.</p>
      <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
      <p v-if="message" class="text-sm text-emerald-600">{{ message }}</p>
      <button class="btn-primary" :disabled="saving || Boolean(percentageError)">{{ benefit ? "Guardar y enviar a revisión" : "Crear beneficio" }}</button>
    </form>
  </div>
</template>
