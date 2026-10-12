<script setup lang="ts">
import { authService } from "~/services/auth.service";

definePageMeta({ layout: "dashboard" });

const authStore = useAuthStore();

const TABS = [
  { key: "principal", label: "Datos principales" },
  { key: "ubicacion", label: "Ubicación", optional: true },
  { key: "festejos", label: "Festejos", optional: true },
  { key: "conocernos", label: "Cuéntanos de ti", optional: true },
];
const tab = ref("principal");

const form = reactive({
  first_name: authStore.user?.first_name || "",
  last_name: authStore.user?.last_name || "",
  document_id: authStore.user?.document_id || "",
});
// Una vez guardada, la cédula solo la cambia el equipo admin.
const documentLocked = computed(() => Boolean(authStore.user?.document_id));

const location = ref({
  department: authStore.user?.department || "",
  city: authStore.user?.city || "",
  address: authStore.user?.address || "",
});
const about = ref(profileAboutFromUser(authStore.user));
const festejosForm = ref(festejosFormFromUser(authStore.user));
const loading = ref(false);
const success = ref(false);
const error = ref("");

async function handleSubmit() {
  success.value = false;
  error.value = "";

  if (!form.first_name.trim() || !form.last_name.trim()) {
    tab.value = "principal";
    error.value = "El nombre y el apellido son obligatorios.";
    return;
  }
  if (festejosForm.value.children.some((child) => !child.name.trim() || !child.birth_date)) {
    tab.value = "festejos";
    error.value = "Completa el nombre y la fecha de cada hijo/a, o quítalo.";
    return;
  }

  loading.value = true;
  try {
    await authStore.updateProfile({
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      ...(!documentLocked.value && form.document_id.trim() ? { document_id: form.document_id.trim() } : {}),
      ...location.value,
      ...festejosPayload(festejosForm.value),
      member_profile: profileAboutPayload(about.value),
    });
    festejosForm.value = festejosFormFromUser(authStore.user);
    form.document_id = authStore.user?.document_id || "";
    success.value = true;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

// ---- Foto de perfil: se sube de inmediato (sale en comentarios y festejos) ----
const photoBusy = ref(false);
const photoError = ref("");

async function changePhoto(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  photoBusy.value = true;
  photoError.value = "";
  try {
    const { data } = await authService.uploadPhoto(file);
    authStore.setUser(data);
  } catch (err) {
    photoError.value = useErrorMessage(err);
  } finally {
    photoBusy.value = false;
  }
}

async function dropPhoto() {
  photoBusy.value = true;
  photoError.value = "";
  try {
    const { data } = await authService.removePhoto();
    authStore.setUser(data);
  } catch (err) {
    photoError.value = useErrorMessage(err);
  } finally {
    photoBusy.value = false;
  }
}

const passwordForm = reactive({ current_password: "", new_password: "", confirm_password: "" });
const passwordLoading = ref(false);
const passwordSuccess = ref(false);
const passwordError = ref("");

async function handlePasswordSubmit() {
  passwordError.value = "";
  passwordSuccess.value = false;
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    passwordError.value = "Las contraseñas nuevas no coinciden.";
    return;
  }
  passwordLoading.value = true;
  try {
    await authService.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    });
    passwordSuccess.value = true;
    passwordForm.current_password = "";
    passwordForm.new_password = "";
    passwordForm.confirm_password = "";
  } catch (err) {
    passwordError.value = useErrorMessage(err);
  } finally {
    passwordLoading.value = false;
  }
}
</script>

<template>
  <div class="max-w-4xl">
    <h1 class="text-2xl font-bold text-ink">Mi perfil</h1>
    <p class="mt-1 text-sm text-muted">Actualiza tus datos. Solo los datos principales son obligatorios.</p>

    <div class="card mt-6 p-6">
      <form class="space-y-5" novalidate @submit.prevent="handleSubmit">
        <ProfileTabs v-model="tab" :tabs="TABS" />

        <!-- DATOS PRINCIPALES -->
        <div v-show="tab === 'principal'" class="space-y-4">
          <div class="flex flex-wrap items-center gap-4">
            <UserAvatar :src="authStore.user?.photo" :name="authStore.user?.first_name || authStore.user?.email" size="xl" />
            <div>
              <p class="text-sm font-medium text-ink">Tu foto</p>
              <p class="text-xs text-muted">Se muestra junto a tus comentarios en el blog y en tu festejo de cumpleaños.</p>
              <div class="mt-2 flex flex-wrap items-center gap-2">
                <label class="btn-outline cursor-pointer !px-3 !py-1.5 text-xs" :class="photoBusy && 'pointer-events-none opacity-60'">
                  {{ photoBusy ? "Subiendo..." : authStore.user?.photo ? "Cambiar foto" : "Subir foto" }}
                  <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="changePhoto" />
                </label>
                <button v-if="authStore.user?.photo" type="button" class="btn-ghost !px-3 !py-1.5 text-xs text-rose-500" :disabled="photoBusy" @click="dropPhoto">
                  Quitar
                </button>
              </div>
              <p v-if="photoError" class="mt-1 text-xs text-rose-500">{{ photoError }}</p>
            </div>
          </div>

          <div class="grid gap-3 sm:grid-cols-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Nombre</label>
              <input v-model="form.first_name" type="text" class="field" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Apellido</label>
              <input v-model="form.last_name" type="text" class="field" />
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
              <input :value="authStore.user?.email" type="email" disabled class="field bg-line/40 text-muted" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">Teléfono (WhatsApp)</label>
              <input :value="authStore.user?.whatsapp" type="text" disabled class="field bg-line/40 text-muted" />
            </div>
          </div>
          <p class="text-xs text-muted">
            Para cambiar tu teléfono<template v-if="documentLocked"> o tu cédula</template>, escribe al equipo admin.
            La cédula solo la ve el equipo admin.
          </p>
          <p v-if="!documentLocked" class="rounded-xl2 bg-gold-light px-3 py-2 text-xs text-gold-dark">
            Para acceder a descuentos y promociones exclusivas para la tribu, debes registrar tu cédula.
          </p>
        </div>

        <div v-show="tab === 'ubicacion'">
          <ProfileLocationFields v-model="location" />
        </div>

        <div v-show="tab === 'festejos'">
          <FestejosDataForm v-model="festejosForm" optional-birth-date photos />
        </div>

        <div v-show="tab === 'conocernos'">
          <ProfileAboutFields v-model="about" />
        </div>

        <p v-if="success" class="text-sm text-emerald-600">Perfil actualizado.</p>
        <p v-if="error" class="text-sm text-rose-500">{{ error }}</p>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? "Guardando..." : "Guardar cambios" }}
        </button>
      </form>
    </div>

    <div class="card mt-6 p-6">
      <h2 class="text-lg font-semibold text-ink">Cambiar contraseña</h2>
      <form class="mt-4 grid gap-3 sm:grid-cols-3" @submit.prevent="handlePasswordSubmit">
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña actual</label>
          <input v-model="passwordForm.current_password" type="password" required class="field" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Contraseña nueva</label>
          <input v-model="passwordForm.new_password" type="password" required minlength="8" class="field" placeholder="Mínimo 8 caracteres" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-ink">Confirmar contraseña nueva</label>
          <input v-model="passwordForm.confirm_password" type="password" required minlength="8" class="field" />
        </div>
        <div class="sm:col-span-3">
          <p v-if="passwordSuccess" class="mb-2 text-sm text-emerald-600">Contraseña actualizada.</p>
          <p v-if="passwordError" class="mb-2 text-sm text-rose-500">{{ passwordError }}</p>
          <button type="submit" class="btn-primary" :disabled="passwordLoading">
            {{ passwordLoading ? "Guardando..." : "Cambiar contraseña" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
