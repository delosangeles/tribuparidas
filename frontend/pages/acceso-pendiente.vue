<script setup lang="ts">
import { userService } from "~/services/user.service";

// Cuenta activa pero aún sin aprobar: la tribu es un espacio privado y solo
// entra quien pertenece al grupo de WhatsApp (lo confirma un administrador).
definePageMeta({ layout: false });

const authStore = useAuthStore();
const { public: config } = useRuntimeConfig();

const sending = ref(false);
const checking = ref(false);
const message = ref("");
const error = ref("");

const firstName = computed(() => authStore.user?.first_name || "");
const whatsappUrl = computed(() => {
  const number = String(config.accessWhatsapp || "").replace(/\D/g, "");
  if (!number) return "";
  const text = encodeURIComponent(
    `Hola, soy ${authStore.user?.first_name ?? ""} ${authStore.user?.last_name ?? ""} (${authStore.user?.email ?? ""}). ` +
      "Quiero que aprueben mi acceso a la página de Tribu Paridas."
  );
  return `https://wa.me/${number}?text=${text}`;
});

async function requestAccess() {
  sending.value = true;
  error.value = message.value = "";
  try {
    message.value = (await userService.requestAccess()).data.detail;
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    sending.value = false;
  }
}

// "Ya me aprobaron": se vuelve a consultar la cuenta; si ya está aprobada, entra.
async function checkAgain() {
  checking.value = true;
  error.value = message.value = "";
  try {
    await authStore.fetchMe();
    if (authStore.user?.is_approved) return navigateTo("/");
    message.value = "Todavía no te han aprobado. Escríbenos por WhatsApp para que confirmemos que estás en el grupo.";
  } finally {
    checking.value = false;
  }
}

async function logout() {
  await authStore.logout();
  await navigateTo("/login");
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-vanilla px-4 py-10">
    <div class="card w-full max-w-md space-y-5 p-8 text-center">
      <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="mx-auto h-16 w-16" />
      <div>
        <h1 class="text-2xl font-bold text-ink">¡Hola{{ firstName ? `, ${firstName}` : "" }}!</h1>
        <p class="mt-2 text-sm text-muted">
          Tu cuenta ya está creada, pero esta es una comunidad privada: <strong class="text-ink">debes pertenecer al grupo de WhatsApp de la tribu</strong>
          para entrar a la página.
        </p>
        <p class="mt-2 text-sm text-muted">Pide tu acceso y un administrador confirmará que estás en el grupo para aprobarte.</p>
      </div>

      <div class="space-y-2">
        <a v-if="whatsappUrl" :href="whatsappUrl" target="_blank" rel="noopener" class="btn-primary w-full">
          <AppIcon name="whatsapp" :size="18" /> Escribir por WhatsApp para solicitar mi acceso
        </a>
        <button class="w-full" :class="whatsappUrl ? 'btn-outline' : 'btn-primary'" :disabled="sending" @click="requestAccess">
          {{ sending ? "Enviando..." : "Avisar al equipo que quiero entrar" }}
        </button>
        <button class="btn-ghost w-full" :disabled="checking" @click="checkAgain">Ya me aprobaron, entrar</button>
      </div>

      <p v-if="message" class="text-sm text-emerald-600" role="status">{{ message }}</p>
      <p v-if="error" class="text-sm text-rose-500" role="alert">{{ error }}</p>

      <button class="text-xs text-muted underline hover:text-gold" @click="logout">Cerrar sesión</button>
    </div>
  </div>
</template>
