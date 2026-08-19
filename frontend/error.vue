<script setup lang="ts">
const props = defineProps<{ error: { statusCode: number; statusMessage?: string } }>();
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 bg-vanilla px-4 text-center">
    <span class="flex h-16 w-16 items-center justify-center rounded-full bg-gold-light text-gold">
      <AppIcon name="x-circle" :size="32" />
    </span>
    <h1 class="text-3xl font-bold text-ink">{{ error.statusCode }}</h1>
    <p class="text-muted">{{ error.statusMessage || "Algo salió mal." }}</p>
    <NuxtLink to="/" class="btn-primary">Volver al inicio</NuxtLink>
  </div>
</template>
