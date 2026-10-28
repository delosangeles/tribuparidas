<script setup lang="ts">
import { portalService } from "~/services/portal.service";
import type { CardBlocker, MemberNotice, MyCard } from "~/types";

definePageMeta({ middleware: "member-card" });

const REFRESH_MARGIN_SECONDS = 10;

const card = ref<MyCard | null>(null);
const notices = ref<MemberNotice[]>([]);
const secondsLeft = ref(0);
const error = ref("");
const consentChecked = ref(false);
const savingConsent = ref(false);
let tick: ReturnType<typeof setInterval> | null = null;
let expiresAt = 0;

const BLOCKERS: Record<CardBlocker, string> = {
  not_member: "Tu cuenta no es de usuaria de la página.",
  inactive: "Tu cuenta aún no está activa.",
  membership_inactive: "Tu membresía está suspendida. Escríbele al equipo de la tribu.",
  missing_document: "Para tener tu tarjeta debes registrar tu cédula en Mi perfil.",
  consent_required: "Falta aceptar que compartamos tus datos con los emprendimientos.",
};

async function load() {
  try {
    card.value = (await portalService.card()).data;
    error.value = "";
    if (card.value.token) expiresAt = Date.now() + (card.value.expires_in ?? 90) * 1000;
  } catch (err) {
    error.value = useErrorMessage(err);
  }
}

function refreshIfNeeded() {
  secondsLeft.value = Math.max(0, Math.round((expiresAt - Date.now()) / 1000));
  if (card.value?.eligible && !document.hidden && secondsLeft.value <= REFRESH_MARGIN_SECONDS) load();
}

onMounted(async () => {
  await load();
  notices.value = (await portalService.notices()).data.results;
  tick = setInterval(refreshIfNeeded, 1000);
  document.addEventListener("visibilitychange", refreshIfNeeded);
});
onBeforeUnmount(() => {
  if (tick) clearInterval(tick);
  document.removeEventListener("visibilitychange", refreshIfNeeded);
});

async function acceptConsent() {
  savingConsent.value = true;
  try {
    await portalService.acceptConsent();
    await load();
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    savingConsent.value = false;
  }
}

const unread = computed(() => notices.value.filter((n) => !n.is_read));
async function dismissNotices() {
  await portalService.markNoticesRead();
  notices.value = notices.value.map((n) => ({ ...n, is_read: true }));
}
const spacedCode = computed(() => (card.value?.code ? `${card.value.code.slice(0, 3)} ${card.value.code.slice(3)}` : ""));
</script>

<template>
  <div class="mx-auto max-w-md space-y-5 px-4 py-6 sm:py-10">
    <header class="text-center">
      <h1 class="text-2xl font-bold text-ink">Mi tarjeta Tribu</h1>
      <p v-if="card" class="text-sm text-muted">{{ card.name }}</p>
    </header>

    <p v-if="error" class="text-center text-sm text-rose-500">{{ error }}</p>

    <div v-if="unread.length" class="card border-gold/40 bg-gold-light/40 p-4" role="status">
      <p v-for="n in unread" :key="n.id" class="text-sm text-ink">{{ n.message }}</p>
      <button class="btn-ghost mt-1 !px-0 text-xs" @click="dismissNotices">Entendido</button>
    </div>

    <template v-if="card">
      <section v-if="card.eligible" class="card space-y-3 p-6 text-center">
        <span class="badge-approved mx-auto">{{ card.membership_active ? "Membresía activa" : "Membresía suspendida" }}</span>
        <QrCard v-if="card.token" :value="card.token" :size="240" class="mx-auto" />
        <p class="text-xs text-muted">Muéstrasela a la dueña del emprendimiento. Se renueva sola.</p>
        <div>
          <p class="text-xs uppercase tracking-wide text-muted">Código de respaldo</p>
          <p class="font-mono text-3xl font-bold tracking-widest text-ink" aria-live="off">{{ spacedCode }}</p>
        </div>
        <div class="mx-auto h-1.5 w-full max-w-[15rem] overflow-hidden rounded-full bg-gold-light" aria-hidden="true">
          <div class="h-full bg-gold transition-all" :style="{ width: `${Math.min(100, (secondsLeft / (card.expires_in || 90)) * 100)}%` }" />
        </div>
      </section>

      <section v-else class="card space-y-3 p-6">
        <p class="font-semibold text-ink">Aún no puedes usar tu tarjeta</p>
        <ul class="list-disc space-y-1 pl-5 text-sm text-muted">
          <li v-for="b in card.blockers" :key="b">{{ BLOCKERS[b] }}</li>
        </ul>
        <NuxtLink v-if="card.blockers.includes('missing_document')" to="/dashboard/settings" class="btn-outline">Ir a Mi perfil</NuxtLink>

        <form v-if="card.blockers.includes('consent_required')" class="space-y-3 border-t border-line pt-3" @submit.prevent="acceptConsent">
          <label class="flex items-start gap-2 text-sm text-ink">
            <input v-model="consentChecked" type="checkbox" class="mt-0.5 h-4 w-4 accent-gold" />
            <span>
              Autorizo a Tribu Paridas a compartir mi <strong>nombre, teléfono y correo</strong> con los emprendimientos de la tribu
              cuando abro su tarjeta o uso un descuento, únicamente para aplicarme el beneficio (Ley 1581 de 2012). Puedo
              retirar esta autorización cuando quiera. Mi cédula no se comparte.
            </span>
          </label>
          <button class="btn-primary" :disabled="!consentChecked || savingConsent">Aceptar y activar mi tarjeta</button>
        </form>
      </section>

      <section>
        <h2 class="mb-2 font-semibold text-ink">Tus beneficios</h2>
        <EmptyState v-if="!card.benefits.length" icon="gift" title="Aún no hay beneficios publicados" description="Pronto verás aquí los descuentos de los emprendimientos de la tribu." />
        <ul class="space-y-2">
          <li v-for="b in card.benefits" :key="b.business_id">
            <NuxtLink :to="`/emprendimientos/${b.slug}`" class="card flex items-center gap-3 p-3 transition hover:border-gold">
              <span class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gold-light text-gold">
                <img v-if="b.logo" :src="b.logo" :alt="b.name" class="h-full w-full object-cover" />
                <AppIcon v-else name="briefcase" :size="20" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate font-medium text-ink">{{ b.name }}</span>
                <span class="block truncate text-xs text-muted">{{ b.conditions || "Una vez al día" }}</span>
              </span>
              <span class="text-lg font-bold text-gold-dark">{{ b.percentage }}%</span>
            </NuxtLink>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>
