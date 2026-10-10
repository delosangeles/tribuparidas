<script setup lang="ts">
// Aviso de bienvenida para quienes ya tienen datos precargados del Excel de
// inscripción: "tenemos información nueva para ti". Pueden revisarla,
// corregirla y confirmarla. "Más tarde" lo oculta durante esta sesión; vuelve
// a salir al próximo ingreso hasta que se confirme.
const authStore = useAuthStore();
const LATER_KEY = "tp_confirm_later";

const TABS = [
  { key: "datos", label: "Tus datos" },
  { key: "ubicacion", label: "Ubicación" },
  { key: "festejos", label: "Festejos" },
  { key: "conocernos", label: "Cuéntanos de ti" },
];
const tab = ref("datos");

const postponed = ref(false);
const done = ref(false);
const loading = ref(false);
const error = ref("");

const form = reactive({ first_name: "", last_name: "", document_id: "" });
const location = ref({ department: "", city: "", address: "" });
const about = ref(emptyProfileAbout());
const festejosForm = ref(emptyFestejosForm());

const user = computed(() => authStore.user);
const needsConfirmation = computed(() => authStore.isAuthenticated && Boolean(user.value?.needs_data_confirmation));
const show = computed(() => (needsConfirmation.value && !postponed.value) || done.value);
const documentLocked = computed(() => Boolean(user.value?.document_id));
const writtenLocation = computed(() => user.value?.member_profile?.location || "");

function seed() {
  const current = user.value;
  form.first_name = current?.first_name || "";
  form.last_name = current?.last_name || "";
  form.document_id = current?.document_id || "";
  location.value = { department: current?.department || "", city: current?.city || "", address: current?.address || "" };
  about.value = profileAboutFromUser(current ?? null);
  festejosForm.value = festejosFormFromUser(current ?? null);
}

watch(() => user.value?.id, seed, { immediate: true });

onMounted(() => {
  try {
    postponed.value = sessionStorage.getItem(LATER_KEY) === "1";
  } catch {
    postponed.value = false;
  }
});

function later() {
  postponed.value = true;
  try {
    sessionStorage.setItem(LATER_KEY, "1");
  } catch {
    // sin sessionStorage solo se oculta hasta recargar
  }
}

async function confirm() {
  error.value = "";
  if (!form.first_name.trim() || !form.last_name.trim()) {
    tab.value = "datos";
    error.value = "Necesitamos tu nombre y tu apellido.";
    return;
  }
  if (festejosForm.value.children.some((child) => !child.name.trim() || !child.birth_date)) {
    tab.value = "festejos";
    error.value = "Completa el nombre y la fecha de cada hijo/a, o quítalo.";
    return;
  }
  if (festejosForm.value.pregnant && !festejosForm.value.due_date) {
    tab.value = "festejos";
    error.value = "Indica la fecha probable de parto, o desmarca el embarazo.";
    return;
  }

  loading.value = true;
  try {
    done.value = true; // se muestra el agradecimiento aunque el aviso ya no sea necesario
    await authStore.updateProfile({
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      ...(!documentLocked.value && form.document_id.trim() ? { document_id: form.document_id.trim() } : {}),
      ...location.value,
      ...festejosPayload(festejosForm.value),
      member_profile: profileAboutPayload(about.value),
      confirm_data: true,
    });
  } catch (err) {
    done.value = false;
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function close() {
  done.value = false;
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-[60] flex items-center justify-center overflow-y-auto bg-ink/50 px-3 py-6" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <div class="card relative max-h-[94vh] w-full max-w-3xl overflow-y-auto p-0">
        <!-- gracias -->
        <div v-if="done" class="px-6 py-14 text-center">
          <span class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gold-light text-gold">
            <AppIcon name="heart" :size="30" class="fill-current" />
          </span>
          <h2 class="mt-5 text-2xl font-bold text-ink">¡Gracias, {{ user?.first_name || "mamá" }}!</h2>
          <p class="mx-auto mt-2 max-w-md text-sm text-muted">
            Tus datos quedaron confirmados. Así podemos cuidar mejor la tribu y celebrar contigo cada mesversario y cada cumpleaños. 💛
          </p>
          <button type="button" class="btn-primary mt-6" @click="close">Entrar a la tribu</button>
        </div>

        <template v-else>
          <header class="relative overflow-hidden bg-gradient-to-br from-gold-light via-vanilla to-white px-6 pb-5 pt-7 text-center">
            <span class="pointer-events-none absolute -left-3 top-3 text-gold/30" aria-hidden="true"><AppIcon name="flower" :size="64" /></span>
            <span class="pointer-events-none absolute -right-2 bottom-2 text-gold/30" aria-hidden="true"><AppIcon name="heart" :size="56" /></span>
            <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-white text-gold shadow-soft">
              <AppIcon name="heart" :size="24" class="fill-current" />
            </span>
            <h2 id="confirm-title" class="mt-3 text-2xl font-bold text-ink">¡Hola, {{ user?.first_name || "mamá" }}! 💛</h2>
            <p class="mx-auto mt-2 max-w-xl text-sm text-muted">
              Estamos organizando la tribu para cuidarla mejor y celebrar contigo cada mesversario y cada cumpleaños.
              <strong class="text-ink">Tenemos información nueva para ti:</strong> son los datos que nos compartiste
              cuando te inscribiste. Revísalos, corrígelos si hace falta y confírmalos.
            </p>
          </header>

          <form class="space-y-5 px-5 pb-5 pt-4 sm:px-6" novalidate @submit.prevent="confirm">
            <ProfileTabs v-model="tab" :tabs="TABS" />

            <div v-show="tab === 'datos'" class="space-y-3">
              <div class="grid gap-3 sm:grid-cols-3">
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
                  <input v-model="form.first_name" type="text" class="field" autocomplete="given-name" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
                  <input v-model="form.last_name" type="text" class="field" autocomplete="family-name" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Cédula <span class="font-normal text-muted">(opcional)</span></label>
                  <input
                    v-model="form.document_id"
                    type="text"
                    maxlength="30"
                    class="field"
                    :disabled="documentLocked"
                    :class="documentLocked && 'bg-line/40 text-muted'"
                    placeholder="Sin puntos ni espacios"
                  />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Correo</label>
                  <input :value="user?.email" type="email" disabled class="field bg-line/40 text-muted" />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-ink">Teléfono (WhatsApp)</label>
                  <input :value="user?.whatsapp" type="text" disabled class="field bg-line/40 text-muted" />
                </div>
              </div>
              <p v-if="!documentLocked" class="rounded-xl2 bg-gold-light px-3 py-2 text-xs text-gold-dark">
                Si quieres acceder a descuentos y promociones exclusivas para la tribu, debes registrar tu cédula.
              </p>
              <p class="text-xs text-muted">Para cambiar tu teléfono, escribe al equipo admin.</p>
            </div>

            <div v-show="tab === 'ubicacion'" class="space-y-3">
              <p v-if="writtenLocation" class="rounded-xl2 bg-vanilla px-3 py-2 text-xs text-muted">
                En el formulario nos escribiste: <strong class="text-ink">«{{ writtenLocation }}»</strong>. Elige tu departamento y ciudad para ubicarte mejor.
              </p>
              <ProfileLocationFields v-model="location" />
            </div>

            <div v-show="tab === 'festejos'">
              <FestejosDataForm v-model="festejosForm" optional-birth-date photos />
            </div>

            <div v-show="tab === 'conocernos'">
              <ProfileAboutFields v-model="about" />
            </div>

            <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>

            <div class="flex flex-wrap items-center justify-end gap-2 border-t border-line pt-4">
              <button type="button" class="btn-ghost text-sm" @click="later">Más tarde</button>
              <button type="submit" class="btn-primary" :disabled="loading">
                {{ loading ? "Guardando..." : "Confirmar mis datos" }}
              </button>
            </div>
          </form>
        </template>
      </div>
    </div>
  </Teleport>
</template>
