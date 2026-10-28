<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { RedeemError, RedeemPreview } from "~/types";

definePageMeta({ layout: "portal", middleware: "portal" });

const { businessId } = usePortalBusiness(() => reset());

const code = ref("");
const loading = ref(false);
const preview = ref<RedeemPreview | null>(null);
const failure = ref<RedeemError | null>(null);
const done = ref<{ name: string; percentage: number } | null>(null);
const scanner = ref<{ start: () => void; stop: () => void } | null>(null);

function reset() {
  code.value = "";
  preview.value = null;
  failure.value = null;
  done.value = null;
}

function fail(err: unknown) {
  const data = (err as { response?: { data?: RedeemError; status?: number } }).response;
  if (data?.status === 429) {
    failure.value = { code: "rate_limited", detail: "Demasiados intentos. Espera un momento." };
  } else if (data?.data?.code) {
    failure.value = data.data;
  } else {
    failure.value = { code: "error", detail: useErrorMessage(err) };
  }
}

async function check(payload: { token?: string; code?: string }) {
  loading.value = true;
  failure.value = null;
  preview.value = null;
  try {
    preview.value = (await portalService.redeemPreview(businessId.value, payload)).data;
  } catch (err) {
    fail(err);
  } finally {
    loading.value = false;
  }
}

const onScan = (value: string) => check({ token: value });
const submitCode = () => check({ code: code.value.replace(/\D/g, "") });

async function confirm() {
  if (!preview.value) return;
  loading.value = true;
  try {
    const { data } = await portalService.redeemConfirm(businessId.value, preview.value.ticket);
    done.value = { name: data.member.name, percentage: data.percentage };
    preview.value = null;
  } catch (err) {
    fail(err);
    preview.value = null;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="mx-auto max-w-lg space-y-5">
    <header>
      <h1 class="text-2xl font-bold text-ink">Escanear tarjeta</h1>
      <p class="text-sm text-muted">Lee el QR de la usuaria o escribe su código de 6 dígitos. No necesitas su cédula ni su teléfono.</p>
    </header>

    <div v-if="done" class="card space-y-3 p-5 text-center">
      <AppIcon name="check-circle" :size="40" class="mx-auto text-emerald-600" />
      <p class="text-lg font-semibold text-ink">¡Descuento aplicado!</p>
      <p class="text-sm text-muted">{{ done.percentage }}% para {{ done.name }}. Ya le avisamos.</p>
      <button class="btn-primary" @click="reset">Escanear otra</button>
    </div>

    <template v-else>
      <div v-if="!preview" class="card space-y-4 p-5">
        <QrScanner ref="scanner" @scan="onScan" />
        <form class="flex gap-2" @submit.prevent="submitCode">
          <input
            v-model="code"
            inputmode="numeric"
            maxlength="7"
            autocomplete="off"
            class="input"
            placeholder="Código de 6 dígitos"
            aria-label="Código de respaldo"
          />
          <button class="btn-primary" :disabled="loading || code.replace(/\D/g, '').length !== 6">Validar</button>
        </form>
      </div>

      <div v-if="failure" class="card border-rose-200 bg-rose-50 p-5" role="alert">
        <p class="flex items-center gap-2 font-semibold text-rose-600"><AppIcon name="x-circle" :size="20" /> {{ failure.detail }}</p>
        <p v-if="failure.member" class="mt-1 text-sm text-rose-500">{{ failure.member.name }}</p>
      </div>

      <div v-if="preview" class="card space-y-3 p-5">
        <p class="text-xs font-semibold uppercase tracking-wide text-muted">Usuaria</p>
        <p class="text-xl font-bold text-ink">{{ preview.member.name }}</p>
        <p class="badge-approved w-fit">{{ preview.member.status }}</p>
        <div class="rounded-xl2 border border-gold/30 bg-gold-light/40 p-4">
          <p class="text-2xl font-bold text-gold-dark">{{ preview.benefit.percentage }}% de descuento</p>
          <p v-if="preview.benefit.conditions" class="mt-1 text-sm text-ink">{{ preview.benefit.conditions }}</p>
        </div>
        <div class="flex gap-2">
          <button class="btn-primary flex-1" :disabled="loading" @click="confirm">Aplicar descuento</button>
          <button class="btn-outline" :disabled="loading" @click="reset">Cancelar</button>
        </div>
      </div>
    </template>
  </div>
</template>
