<script setup lang="ts">
const props = defineProps<{ modelValue: number }>();
const emit = defineEmits<{ (e: "update:modelValue", value: number): void }>();

const hovered = ref<number | null>(null);
const stars = [1, 2, 3, 4, 5];
</script>

<template>
  <div class="flex items-center gap-1" @mouseleave="hovered = null">
    <button
      v-for="star in stars"
      :key="star"
      type="button"
      class="text-amber-400 transition"
      :class="(hovered ?? props.modelValue) >= star ? 'opacity-100' : 'opacity-30'"
      @mouseenter="hovered = star"
      @click="emit('update:modelValue', star)"
    >
      <AppIcon name="star" :size="26" class="fill-current" />
    </button>
  </div>
</template>
