<script setup lang="ts">
import { authService } from "~/services/auth.service";

const authStore = useAuthStore();
const route = useRoute();

const mode = ref<"login" | "register">("login");

// ====================
// LOGIN
// ====================

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function handleLogin() {
  loading.value = true;
  error.value = "";

  try {
    await authStore.login(email.value, password.value);

    const redirect =
      (route.query.redirect as string) ||
      (authStore.isAdmin ? "/admin" : "/");

    await navigateTo(redirect);
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

// ====================
// RECUPERAR CONTRASEÑA
// ====================

const showForgot = ref(false);
const forgotEmail = ref("");
const forgotLoading = ref(false);
const forgotSent = ref(false);
const forgotError = ref("");

function openForgot() {
  forgotEmail.value = email.value;
  forgotSent.value = false;
  forgotError.value = "";
  showForgot.value = true;
}

async function submitForgot() {
  forgotLoading.value = true;
  forgotError.value = "";

  try {
    await authService.requestPasswordReset(forgotEmail.value);
    forgotSent.value = true;
  } catch (err) {
    forgotError.value = useErrorMessage(err);
  } finally {
    forgotLoading.value = false;
  }
}

// ====================
// REGISTRO
// ====================

const form = reactive({
  first_name: "",
  last_name: "",
  document_id: "",
  email: "",
  whatsapp: "",
  password: "",
});

// Obligatorio: la pestaña "Datos principales". El resto es opcional.
const REGISTER_TABS = [
  { key: "principal", label: "Datos principales" },
  { key: "ubicacion", label: "Ubicación", optional: true },
  { key: "festejos", label: "Festejos", optional: true },
  { key: "conocernos", label: "Cuéntanos de ti", optional: true },
];
const registerTab = ref("principal");

const location = ref({ department: "", city: "", address: "" });
const about = ref(emptyProfileAbout());
const festejosForm = ref(emptyFestejosForm());
const registerLoading = ref(false);
const registerError = ref("");
const submitted = ref(false);
const registerMessage = ref("");

// Se valida a mano (el formulario es `novalidate`) para poder llevar a la
// persona a la pestaña donde está el problema, aunque esté oculta.
function validateRegister(): string | null {
  const required = [form.first_name, form.last_name, form.email, form.whatsapp, form.password];
  if (required.some((value) => !value.trim())) {
    registerTab.value = "principal";
    return "Completa nombre, apellido, teléfono, correo y contraseña.";
  }
  if (!new RegExp(PHONE_PATTERN).test(form.whatsapp.trim())) {
    registerTab.value = "principal";
    return PHONE_ERROR_MESSAGE;
  }
  if (form.password.length < 8) {
    registerTab.value = "principal";
    return "La contraseña debe tener mínimo 8 caracteres.";
  }
  if (festejosForm.value.children.some((child) => !child.name.trim() || !child.birth_date)) {
    registerTab.value = "festejos";
    return "Completa el nombre y la fecha de cada hijo/a, o quítalo.";
  }
  if (festejosForm.value.pregnant && !festejosForm.value.due_date) {
    registerTab.value = "festejos";
    return "Indica la fecha probable de parto, o desmarca el embarazo.";
  }
  return null;
}

async function handleRegister() {
  registerError.value = "";
  const problem = validateRegister();
  if (problem) {
    registerError.value = problem;
    return;
  }

  registerLoading.value = true;

  try {
    const filledLocation = Object.fromEntries(Object.entries(location.value).filter(([, value]) => value));
    const data = await authStore.register({
      ...form,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      ...(form.document_id.trim() ? { document_id: form.document_id.trim() } : {}),
      email: form.email.trim(),
      whatsapp: form.whatsapp.trim(),
      ...filledLocation,
      ...festejosPayload(festejosForm.value),
      member_profile: profileAboutPayload(about.value, true),
    });

    registerMessage.value = data.detail;
    submitted.value = true;
  } catch (err) {
    registerError.value = useErrorMessage(err);
  } finally {
    registerLoading.value = false;
  }
}

function showLogin() {
  mode.value = "login";
  error.value = "";
}

function showRegister() {
  mode.value = "register";
  registerError.value = "";
}
</script>

<template>
  <div
    class="mx-auto flex min-h-[80vh] flex-col items-center px-4 py-16"
    :class="mode === 'register' ? 'max-w-3xl' : 'max-w-md'"
  >
    <!-- LOGO -->
    <NuxtLink to="/">
      <BrandMark />
    </NuxtLink>

    <!-- ==================== -->
    <!-- LOGIN -->
    <!-- ==================== -->

    <template v-if="mode === 'login'">
      <div class="card mt-8 w-full p-6">
        <h1 class="text-xl font-bold text-ink">
          Iniciar sesión
        </h1>

        <p class="mt-1 text-sm text-muted">
          Bienvenida de nuevo a la comunidad.
        </p>

        <form
          class="mt-6 space-y-4"
          @submit.prevent="handleLogin"
        >
          <!-- EMAIL -->
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              Email
            </label>

            <input
              v-model="email"
              type="email"
              required
              class="field"
              placeholder="tu@email.com"
            />
          </div>

          <!-- PASSWORD -->
          <div>
            <div class="mb-1 flex items-center justify-between">
              <label class="block text-sm font-medium text-ink">
                Contraseña
              </label>

              <button
                type="button"
                class="text-xs font-semibold text-gold hover:underline"
                @click="openForgot"
              >
                ¿La olvidaste?
              </button>
            </div>

            <input
              v-model="password"
              type="password"
              required
              class="field"
              placeholder="••••••••"
            />
          </div>

          <!-- ERROR -->
          <div v-if="error">
            <p class="text-sm text-rose-500">
              {{ error }}
            </p>

            <p class="mt-1 text-xs text-muted">
              Si te acabas de registrar, tu cuenta puede estar en revisión.
            </p>
          </div>

          <!-- SUBMIT -->
          <button
            type="submit"
            class="btn-primary w-full"
            :disabled="loading"
          >
            {{ loading ? "Ingresando..." : "Iniciar sesión" }}
          </button>
        </form>

        <!-- GO REGISTER -->
        <p class="mt-6 text-center text-sm text-muted">
          ¿No tienes cuenta?

          <button
            type="button"
            class="font-semibold text-gold hover:underline"
            @click="showRegister"
          >
            Regístrate
          </button>
        </p>
      </div>
    </template>

    <!-- ==================== -->
    <!-- REGISTRO -->
    <!-- ==================== -->

    <template v-else>
      <div class="mt-4 text-center">
        <h1 class="text-2xl font-bold text-ink">
          Bienvenida a la tribu
        </h1>

        <p class="mt-1 text-sm text-muted">
          Crea tu cuenta para comenzar.
        </p>
      </div>

      <!-- REGISTRO EXITOSO -->
      <div
        v-if="submitted"
        class="card mt-8 w-full p-6 text-center"
      >
        <span
          class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500"
        >
          <AppIcon
            name="check-circle"
            :size="26"
          />
        </span>

        <p class="mt-4 font-semibold text-ink">
          ¡Registro recibido!
        </p>

        <p class="mt-1 text-sm text-muted">
          {{ registerMessage }}
        </p>

        <button
          type="button"
          class="btn-outline mt-4 inline-flex"
          @click="showLogin"
        >
          Iniciar sesión
        </button>
      </div>

      <!-- FORMULARIO -->
      <div
        v-else
        class="card mt-8 w-full p-6"
      >
        <form
          class="space-y-5"
          novalidate
          @submit.prevent="handleRegister"
        >
          <ProfileTabs
            v-model="registerTab"
            :tabs="REGISTER_TABS"
          />

          <!-- DATOS PRINCIPALES (obligatorios) -->
          <div
            v-show="registerTab === 'principal'"
            class="space-y-3"
          >
            <p class="text-xs text-muted">
              Nombre, apellido, teléfono, correo y contraseña son obligatorios. Lo demás es opcional y puedes completarlo después.
            </p>

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
                <input v-model="form.document_id" type="text" inputmode="numeric" maxlength="30" class="field" placeholder="Sin puntos ni espacios" />
              </div>

              <div>
                <label class="mb-1 block text-sm font-medium text-ink">Teléfono (WhatsApp)</label>
                <input
                  v-model="form.whatsapp"
                  type="text"
                  :pattern="PHONE_PATTERN"
                  :title="PHONE_ERROR_MESSAGE"
                  class="field"
                  placeholder="+57 300 000 0000"
                  autocomplete="tel"
                />
              </div>

              <div>
                <label class="mb-1 block text-sm font-medium text-ink">Correo</label>
                <input v-model="form.email" type="email" class="field" placeholder="tu@email.com" autocomplete="email" />
              </div>

              <div>
                <label class="mb-1 block text-sm font-medium text-ink">Contraseña</label>
                <input v-model="form.password" type="password" minlength="8" class="field" placeholder="Mínimo 8 caracteres" autocomplete="new-password" />
              </div>
            </div>

            <p class="text-xs text-muted">
              Con tu teléfono confirmamos que estás en el grupo de la tribu.
            </p>
            <p class="rounded-xl2 bg-gold-light px-3 py-2 text-xs text-gold-dark">
              <strong>Sobre la cédula:</strong> no es obligatoria, pero si quieres acceder a descuentos y promociones
              exclusivas para la tribu, debes registrarla. Solo la ve el equipo admin.
            </p>
          </div>

          <!-- UBICACIÓN -->
          <div
            v-show="registerTab === 'ubicacion'"
            class="space-y-3"
          >
            <p class="text-xs text-muted">Opcional. Nos ayuda a conectar a las mamás de una misma zona.</p>
            <ProfileLocationFields v-model="location" />
          </div>

          <!-- FESTEJOS -->
          <div
            v-show="registerTab === 'festejos'"
            class="space-y-3"
          >
            <FestejosDataForm v-model="festejosForm" optional-birth-date />
            <p class="text-xs text-muted">
              Las fotos (la tuya y la de cada hijo/a) las puedes subir desde tu perfil cuando tu cuenta esté aprobada.
            </p>
          </div>

          <!-- CUÉNTANOS DE TI -->
          <div v-show="registerTab === 'conocernos'">
            <ProfileAboutFields v-model="about" />
          </div>

          <!-- ERROR -->
          <p
            v-if="registerError"
            class="text-sm text-rose-500"
          >
            {{ registerError }}
          </p>

          <!-- SUBMIT -->
          <button
            type="submit"
            class="btn-primary w-full"
            :disabled="registerLoading"
          >
            {{ registerLoading ? "Enviando..." : "Registrarme" }}
          </button>
        </form>

        <!-- GO LOGIN -->
        <p class="mt-4 text-center text-sm text-muted">
          ¿Ya tienes cuenta?

          <button
            type="button"
            class="font-semibold text-gold hover:underline"
            @click="showLogin"
          >
            Inicia sesión
          </button>
        </p>
      </div>
    </template>

    <!-- ==================== -->
    <!-- RECUPERAR CONTRASEÑA -->
    <!-- ==================== -->

    <Teleport to="body">
      <div
        v-if="showForgot"
        class="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4"
      >
        <div class="card w-full max-w-sm p-6">
          <!-- SUCCESS -->
          <template v-if="forgotSent">
            <span
              class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500"
            >
              <AppIcon
                name="check-circle"
                :size="24"
              />
            </span>

            <p class="mt-4 text-center font-semibold text-ink">
              ¡Listo!
            </p>

            <p class="mt-1 text-center text-sm text-muted">
              Le avisamos al equipo. Te contactarán por WhatsApp para ayudarte
              a recuperar el acceso.
            </p>

            <button
              class="btn-primary mt-6 w-full"
              @click="showForgot = false"
            >
              Cerrar
            </button>
          </template>

          <!-- FORM -->
          <template v-else>
            <p class="text-lg font-semibold text-ink">
              ¿Olvidaste tu contraseña?
            </p>

            <p class="mt-1 text-sm text-muted">
              Escribe tu correo. Le avisamos al equipo de la tribu para que te
              ayude a recuperar el acceso por WhatsApp.
            </p>

            <form
              class="mt-4 space-y-3"
              @submit.prevent="submitForgot"
            >
              <input
                v-model="forgotEmail"
                type="email"
                required
                class="field"
                placeholder="tu@email.com"
              />

              <p
                v-if="forgotError"
                class="text-sm text-rose-500"
              >
                {{ forgotError }}
              </p>

              <div class="flex justify-end gap-2">
                <button
                  type="button"
                  class="btn-ghost"
                  @click="showForgot = false"
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  class="btn-primary"
                  :disabled="forgotLoading"
                >
                  {{ forgotLoading ? "Enviando..." : "Avisar al equipo" }}
                </button>
              </div>
            </form>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>