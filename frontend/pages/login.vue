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
  email: "",
  whatsapp: "",
  password: "",
});

const registerLoading = ref(false);
const registerError = ref("");
const submitted = ref(false);
const registerMessage = ref("");

async function handleRegister() {
  registerLoading.value = true;
  registerError.value = "";

  try {
    const data = await authStore.register({
      ...form,
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
    class="mx-auto flex min-h-[80vh] max-w-md flex-col items-center px-4 py-16"
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
          class="space-y-4"
          @submit.prevent="handleRegister"
        >
          <!-- NOMBRE / APELLIDO -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-ink">
                Nombre
              </label>

              <input
                v-model="form.first_name"
                type="text"
                required
                class="field"
              />
            </div>

            <div>
              <label class="mb-1 block text-sm font-medium text-ink">
                Apellido
              </label>

              <input
                v-model="form.last_name"
                type="text"
                required
                class="field"
              />
            </div>
          </div>

          <!-- EMAIL -->
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              Correo
            </label>

            <input
              v-model="form.email"
              type="email"
              required
              class="field"
              placeholder="tu@email.com"
            />
          </div>

          <!-- WHATSAPP -->
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              WhatsApp
            </label>

            <input
              v-model="form.whatsapp"
              type="text"
              required
              :pattern="PHONE_PATTERN"
              :title="PHONE_ERROR_MESSAGE"
              class="field"
              placeholder="+57 300 000 0000"
            />

            <p class="mt-1 text-xs text-muted">
              Con este número confirmamos que estás en el grupo de la tribu.
            </p>
          </div>

          <!-- PASSWORD -->
          <div>
            <label class="mb-1 block text-sm font-medium text-ink">
              Contraseña
            </label>

            <input
              v-model="form.password"
              type="password"
              required
              minlength="8"
              class="field"
              placeholder="Mínimo 8 caracteres"
            />
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