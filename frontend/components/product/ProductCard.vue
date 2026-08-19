<script setup lang="ts">
import type { Product } from "~/types";

defineProps<{ product: Product }>();

function formatPrice(value: string) {
  const number = Number(value);
  return number.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
}
</script>

<template>
  <div class="card overflow-hidden">
    <div class="aspect-square w-full overflow-hidden bg-gold-light">
      <img v-if="product.image" :src="product.image" :alt="product.name" class="h-full w-full object-cover" />
      <div v-else class="flex h-full w-full items-center justify-center text-gold">
        <AppIcon name="box" :size="28" />
      </div>
    </div>
    <div class="p-4">
      <p class="font-medium text-ink">{{ product.name }}</p>
      <p class="mt-1 text-sm font-semibold text-gold">{{ formatPrice(product.price) }}</p>
    </div>
  </div>
</template>
