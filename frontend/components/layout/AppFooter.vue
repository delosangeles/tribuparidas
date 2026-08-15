<script setup lang="ts">
const year = new Date().getFullYear();
</script>

<template>
  <footer class="mt-16 border-t border-line bg-white">
    <div class="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div class="flex flex-col items-center gap-4 text-center">
        <NuxtLink to="/" class="flex items-center gap-2 text-lg font-bold text-ink">
          <span class="flex h-8 w-8 items-center justify-center rounded-full bg-pink text-white">
            <AppIcon name="heart-filled" :size="16" />
          </span>
          Tribu Paridas
        </NuxtLink>
        <p class="max-w-md text-sm text-muted">
          Un directorio hecho para descubrir y apoyar emprendimientos reales, creados con esfuerzo y pasión.
        </p>
        <div class="flex flex-wrap items-center justify-center gap-3">
          <span class="badge bg-pink-light text-pink">
            <AppIcon name="heart" :size="12" /> Apoya lo local
          </span>
          <span class="badge bg-pink-light text-pink">
            <AppIcon name="heart" :size="12" /> Hecho con amor
          </span>
          <span class="badge bg-pink-light text-pink">
            <AppIcon name="users" :size="12" /> Emprendedoras reales
          </span>
          <span class="badge bg-pink-light text-pink">
            <AppIcon name="heart" :size="12" /> Comunidad que crece
          </span>
        </div>
        <p class="text-xs text-muted">© {{ year }} Tribu Paridas. Todos los derechos reservados.</p>
      </div>
    </div>
  </footer>
</template>
