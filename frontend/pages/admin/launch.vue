<script setup lang="ts">
import { featureFlagService } from "~/services/feature-flag.service";
import type { FeatureFlag } from "~/types";

definePageMeta({ layout: "admin", middleware: "superadmin" });

const { data, refresh } = await useAsyncData("feature-flags-admin", async () => {
  const { data } = await featureFlagService.list();
  return data.results;
});

const flags = computed<FeatureFlag[]>(() => data.value || []);

function formatDateTimeLocal(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60 * 1000);
  return localDate.toISOString().slice(0, 16);
}

// Un input por flag para la fecha/hora que se está editando (aún no guardada).
const form = reactive<Record<string, string>>({});

watch(
  flags,
  (list) => {
    for (const flag of list) {
      if (!(flag.key in form)) {
        form[flag.key] = flag.activate_at ? formatDateTimeLocal(flag.activate_at) : "";
      }
    }
  },
  { immediate: true }
);

const saving = ref<string | null>(null);
const error = ref("");

async function schedule(flag: FeatureFlag) {
  if (!form[flag.key]) return;

  saving.value = flag.key;
  error.value = "";

  try {
    await featureFlagService.update(flag.key, {
      activate_at: new Date(form[flag.key]).toISOString(),
      is_forced_active: false,
    });
    await refresh();
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = null;
  }
}

async function activateNow(flag: FeatureFlag) {
  saving.value = flag.key;
  error.value = "";

  try {
    await featureFlagService.update(flag.key, { is_forced_active: true });
    await refresh();
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = null;
  }
}

async function hideAgain(flag: FeatureFlag) {
  const confirmed = window.confirm(`¿Volver a ocultar "${flag.label}" para todo el mundo excepto el equipo admin?`);
  if (!confirmed) return;

  saving.value = flag.key;
  error.value = "";

  try {
    await featureFlagService.update(flag.key, { activate_at: null, is_forced_active: false });
    form[flag.key] = "";
    await refresh();
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    saving.value = null;
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-ink">Lanzamiento de funcionalidades</h1>
    <p class="mt-1 max-w-2xl text-sm text-muted">
      El código de estas funcionalidades ya puede estar en producción, pero se mantiene oculto para todo el mundo
      (excepto el equipo admin, que puede entrar a prepararlo) hasta la fecha y hora exacta que definas aquí.
    </p>

    <p v-if="error" class="mt-4 text-sm text-rose-500">{{ error }}</p>

    <div class="mt-6 space-y-4">
      <div v-for="flag in flags" :key="flag.key" class="card p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="font-semibold text-ink">{{ flag.label }}</p>
            <p class="mt-1 text-xs text-muted">
              Última actualización: {{ new Date(flag.updated_at).toLocaleString("es-CO") }}
            </p>
          </div>

          <span
            class="inline-flex rounded-full px-3 py-1 text-xs font-semibold"
            :class="flag.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-500'"
          >
            {{ flag.is_active ? "Activo" : "Inactivo" }}
          </span>
        </div>

        <div class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
          <input
            v-model="form[flag.key]"
            type="datetime-local"
            class="field"
            :disabled="flag.is_forced_active"
          />

          <button
            class="btn-primary"
            :disabled="saving === flag.key || !form[flag.key]"
            @click="schedule(flag)"
          >
            Programar
          </button>

          <button
            class="btn-outline"
            :disabled="saving === flag.key || flag.is_active"
            @click="activateNow(flag)"
          >
            Activar ahora
          </button>
        </div>

        <button
          v-if="flag.activate_at || flag.is_forced_active"
          type="button"
          class="btn-ghost mt-3 !px-0 text-xs !text-rose-500"
          :disabled="saving === flag.key"
          @click="hideAgain(flag)"
        >
          Quitar programación (volver a ocultar)
        </button>

        <div v-if="!flag.is_active && flag.activate_at" class="mt-4">
          <CountdownTimer :target="flag.activate_at" label="Se activa en:" />
        </div>
      </div>

      <p v-if="!flags.length" class="text-sm text-muted">No hay funcionalidades registradas todavía.</p>
    </div>
  </div>
</template>
