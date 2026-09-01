<script setup lang="ts">
const props = defineProps<{ target: string; label?: string }>();

const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now();
  }, 1000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const remainingMs = computed(() => Math.max(0, new Date(props.target).getTime() - now.value));
const isOver = computed(() => remainingMs.value <= 0);

const units = computed(() => {
  const total = remainingMs.value;
  return [
    { label: "Días", value: Math.floor(total / 86400000) },
    { label: "Horas", value: Math.floor((total % 86400000) / 3600000) },
    { label: "Min", value: Math.floor((total % 3600000) / 60000) },
    { label: "Seg", value: Math.floor((total % 60000) / 1000) },
  ];
});

function pad(n: number) {
  return String(n).padStart(2, "0");
}
</script>

<template>
  <div class="text-center">
    <p v-if="label" class="mb-3 text-sm font-semibold text-gold-dark">{{ label }}</p>
    <div v-if="!isOver" class="flex justify-center gap-3 sm:gap-4">
      <div v-for="unit in units" :key="unit.label" class="flex w-16 flex-col items-center rounded-xl2 bg-gold-light px-2 py-3 sm:w-20">
        <span class="text-2xl font-bold text-gold-dark sm:text-3xl">{{ pad(unit.value) }}</span>
        <span class="text-[10px] uppercase tracking-wide text-muted">{{ unit.label }}</span>
      </div>
    </div>
    <p v-else class="text-lg font-semibold text-gold-dark">¡Ya llegó la hora!</p>
  </div>
</template>
