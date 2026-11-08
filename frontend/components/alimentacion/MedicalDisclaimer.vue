<script setup lang="ts">
import { MEDICAL_DISCLAIMER } from "~/utils/alimentacion";
</script>

<template>
  <aside
    role="note"
    class="flex items-start gap-3 rounded-xl2 border border-gold-light bg-gold-light/40 px-4 py-3 text-sm text-ink"
  >
    <AppIcon name="shield" :size="18" class="mt-0.5 shrink-0 text-gold-dark" />
    <p><strong class="font-semibold">Importante:</strong> {{ MEDICAL_DISCLAIMER }}</p>
  </aside>
</template>
