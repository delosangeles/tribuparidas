<script setup lang="ts">
const year = new Date().getFullYear();
</script>

<template>
  <footer class="mt-16 border-t border-line bg-white">
    <div class="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div class="flex flex-col items-center gap-4 text-center">
        <NuxtLink to="/">
          <BrandMark />
        </NuxtLink>
        <p class="max-w-md text-sm text-muted">
          Mamás que se eligen, tribu que nos sostiene. Descubre y apoya emprendimientos hechos por otras mamás.
        </p>
        <div class="flex flex-wrap items-center justify-center gap-3">
          <span class="badge bg-gold-light text-gold">
            <AppIcon name="heart" :size="12" /> Apoya lo local
          </span>
          <span class="badge bg-gold-light text-gold">
            <AppIcon name="heart" :size="12" /> Hecho con amor
          </span>
          <span class="badge bg-gold-light text-gold">
            <AppIcon name="users" :size="12" /> Emprendedoras reales
          </span>
          <span class="badge bg-gold-light text-gold">
            <AppIcon name="heart" :size="12" /> Comunidad que crece
          </span>
        </div>
        <p class="text-xs text-muted">© {{ year }} Tribu Paridas. Todos los derechos reservados.</p>
      </div>
    </div>
  </footer>
</template>
