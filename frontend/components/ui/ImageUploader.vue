<script setup lang="ts">
/**
 * Selector de imagen con preview inmediato.
 *
 * - Si se pasa `uploadFn`, la imagen se sube de inmediato (con loading/error)
 *   y se emite `update:modelValue` con la URL final.
 * - Si no, solo se previsualiza y se emite `select` con el File, para que el
 *   formulario padre lo incluya al enviar (ej. crear un emprendimiento).
 */
const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    label?: string;
    shape?: "square" | "circle" | "wide";
    uploadFn?: (file: File) => Promise<string>;
  }>(),
  { modelValue: null, label: "Subir imagen", shape: "square" }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "select", file: File): void;
}>();

const preview = ref<string | null>(props.modelValue);
const loading = ref(false);
const error = ref("");
const inputRef = ref<HTMLInputElement | null>(null);

watch(
  () => props.modelValue,
  (value) => {
    if (value) preview.value = value;
  }
);

const shapeClass = computed(() => {
  if (props.shape === "circle") return "h-28 w-28 rounded-full";
  if (props.shape === "wide") return "h-40 w-full rounded-xl2";
  return "h-32 w-32 rounded-xl2";
});

async function onFileSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  error.value = "";
  preview.value = URL.createObjectURL(file);

  if (!props.uploadFn) {
    emit("select", file);
    return;
  }

  loading.value = true;
  try {
    const url = await props.uploadFn(file);
    preview.value = url;
    emit("update:modelValue", url);
  } catch (err) {
    error.value = useErrorMessage(err);
  } finally {
    loading.value = false;
  }
}

function triggerSelect() {
  inputRef.value?.click();
}
</script>

<template>
  <div>
    <button
      type="button"
      class="group relative flex items-center justify-center overflow-hidden border-2 border-dashed border-line bg-gold-light/40 text-gold transition hover:border-gold"
      :class="shapeClass"
      @click="triggerSelect"
    >
      <img v-if="preview" :src="preview" alt="" class="h-full w-full object-cover" />
      <span v-else class="flex flex-col items-center gap-1 text-xs font-medium">
        <AppIcon name="camera" :size="22" />
        {{ label }}
      </span>

      <span
        v-if="preview"
        class="absolute inset-0 hidden items-center justify-center bg-ink/40 text-white group-hover:flex"
      >
        <AppIcon name="edit" :size="20" />
      </span>

      <span v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/70">
        <span class="h-6 w-6 animate-spin rounded-full border-2 border-gold-light border-t-gold" />
      </span>
    </button>

    <input ref="inputRef" type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="onFileSelected" />
    <p v-if="error" class="mt-2 text-xs text-rose-500">{{ error }}</p>
  </div>
</template>
