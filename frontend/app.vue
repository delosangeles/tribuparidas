<script setup lang="ts">
// Portón de lanzamiento: el sitio ya puede estar desplegado y accesible,
// pero nadie ve el contenido real hasta la hora exacta — así el despliegue
// técnico no tiene que coincidir al segundo con el momento de la revelación.
const LAUNCH_AT = "2026-09-01T19:00:00-05:00";
const BYPASS_KEY = "tp_gate_bypass";
const BYPASS_PARAM = "preview";
const BYPASS_VALUE = "tribu2026";

const now = ref(Date.now());
const hasBypass = ref(false);

if (import.meta.client) {
  const route = useRoute();
  if (route.query[BYPASS_PARAM] === BYPASS_VALUE) {
    localStorage.setItem(BYPASS_KEY, "1");
  }
  hasBypass.value = localStorage.getItem(BYPASS_KEY) === "1";
  setInterval(() => {
    now.value = Date.now();
  }, 1000);
}

const isLive = computed(() => hasBypass.value || now.value >= new Date(LAUNCH_AT).getTime());
</script>

<template>
  <LaunchGate v-if="!isLive" :target="LAUNCH_AT" />
  <NuxtLayout v-else>
    <NuxtPage />
  </NuxtLayout>
</template>
