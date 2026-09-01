<script setup lang="ts">
defineProps<{ target: string }>();
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-vanilla px-4 py-16 text-center">
    <img :src="useAssetUrl('logo-mark.png')" alt="Tribu Paridas" class="h-32 w-32" />
    <h1 class="mt-6 text-2xl font-bold text-ink sm:text-3xl">¡Ya casi estamos listas!</h1>
    <p class="mt-2 max-w-md text-sm text-muted">Nuestra página web abre sus puertas muy pronto. Vuelve en:</p>
    <div class="mt-6">
      <CountdownTimer :target="target" />
    </div>
  </div>
</template>
