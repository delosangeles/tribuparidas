<script setup lang="ts">
/**
 * Select con buscador: muestra la etiqueta de la opción elegida, y al
 * enfocarlo permite escribir para filtrar la lista. Pensado para listas
 * largas (ej. elegir un usuario como autor) donde un <select> nativo es
 * incómodo de navegar.
 */
const props = withDefaults(
  defineProps<{
    modelValue: number | string;
    options: { id: number | string; label: string }[];
    placeholder?: string;
  }>(),
  { placeholder: "Buscar..." }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: number | string): void;
}>();

const query = ref("");
const open = ref(false);
const containerRef = ref<HTMLElement | null>(null);

const selectedLabel = computed(
  () => props.options.find((option) => String(option.id) === String(props.modelValue))?.label || ""
);

const filteredOptions = computed(() => {
  const term = query.value.trim().toLowerCase();
  if (!term) return props.options;
  return props.options.filter((option) => option.label.toLowerCase().includes(term));
});

function openList() {
  open.value = true;
  query.value = "";
}

function select(option: { id: number | string; label: string }) {
  emit("update:modelValue", option.id);
  open.value = false;
  query.value = "";
}

function handleClickOutside(event: MouseEvent) {
  if (open.value && containerRef.value && !containerRef.value.contains(event.target as Node)) {
    open.value = false;
    query.value = "";
  }
}

onMounted(() => document.addEventListener("click", handleClickOutside));
onBeforeUnmount(() => document.removeEventListener("click", handleClickOutside));
</script>

<template>
  <div ref="containerRef" class="relative">
    <input
      type="text"
      class="field"
      :placeholder="placeholder"
      :value="open ? query : selectedLabel"
      @focus="openList"
      @input="(event) => (query = (event.target as HTMLInputElement).value)"
    />

    <div
      v-if="open"
      class="absolute z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-xl2 border border-line bg-white p-1 shadow-soft"
    >
      <button
        v-for="option in filteredOptions"
        :key="option.id"
        type="button"
        class="block w-full rounded-xl2 px-3 py-2 text-left text-sm text-ink transition hover:bg-gold-light hover:text-gold"
        @click="select(option)"
      >
        {{ option.label }}
      </button>

      <p v-if="!filteredOptions.length" class="px-3 py-2 text-sm text-muted">Sin resultados.</p>
    </div>
  </div>
</template>
