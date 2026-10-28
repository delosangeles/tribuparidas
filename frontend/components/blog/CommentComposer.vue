<script setup lang="ts">
// Caja para escribir un comentario, una respuesta o editar uno: texto + foto
// opcional (con vista previa). El padre hace la petición y reinicia la caja
// con `reset()` cuando termina bien.
const props = withDefaults(
  defineProps<{
    placeholder?: string;
    submitLabel?: string;
    busy?: boolean;
    error?: string;
    initialText?: string;
    initialImage?: string | null;
    cancelable?: boolean;
    rows?: number;
  }>(),
  {
    placeholder: "Comparte lo que piensas...",
    submitLabel: "Comentar",
    busy: false,
    error: "",
    initialText: "",
    initialImage: null,
    cancelable: false,
    rows: 3,
  }
);

const emit = defineEmits<{
  (e: "submit", payload: { content: string; image: File | null; removeImage: boolean }): void;
  (e: "cancel"): void;
}>();

const text = ref(props.initialText);
const file = ref<File | null>(null);
const preview = ref<string | null>(props.initialImage);
const removeImage = ref(false);
const localError = ref("");

async function pick(event: Event) {
  const input = event.target as HTMLInputElement;
  const original = input.files?.[0];
  input.value = "";
  if (!original) return;
  let picked: File;
  try {
    picked = await compressImage(original); // HEIC → JPEG y reduce el peso
  } catch (err) {
    localError.value = err instanceof Error ? err.message : "No se pudo procesar la foto.";
    return;
  }
  localError.value = "";
  file.value = picked;
  preview.value = URL.createObjectURL(picked);
  removeImage.value = false;
}

function dropImage() {
  file.value = null;
  preview.value = null;
  removeImage.value = Boolean(props.initialImage);
}

function submit() {
  localError.value = "";
  if (!text.value.trim() && !preview.value) {
    localError.value = "Escribe algo o agrega una foto.";
    return;
  }
  emit("submit", { content: text.value.trim(), image: file.value, removeImage: removeImage.value });
}

function reset() {
  text.value = "";
  file.value = null;
  preview.value = null;
  removeImage.value = false;
  localError.value = "";
}

defineExpose({ reset });
</script>

<template>
  <div class="card p-3 sm:p-4">
    <textarea v-model="text" :rows="rows" maxlength="2000" class="field" :placeholder="placeholder" />

    <div v-if="preview" class="relative mt-2 inline-block">
      <img :src="preview" alt="Vista previa de tu foto" class="max-h-40 rounded-xl2 border border-line object-cover" />
      <button
        type="button"
        class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-ink text-white shadow"
        aria-label="Quitar la foto"
        @click="dropImage"
      >
        <AppIcon name="x" :size="12" />
      </button>
    </div>

    <p v-if="localError || error" class="mt-1 text-xs text-rose-500">{{ localError || error }}</p>

    <div class="mt-2 flex flex-wrap items-center gap-2">
      <label class="btn-outline cursor-pointer !px-3 !py-1.5 text-xs">
        <AppIcon name="camera" :size="14" /> {{ preview ? "Cambiar foto" : "Agregar foto" }}
        <input type="file" :accept="ACCEPT_IMAGES" class="hidden" @change="pick" />
      </label>
      <div class="ml-auto flex gap-2">
        <button v-if="cancelable" type="button" class="btn-ghost !px-3 !py-1.5 text-sm" @click="emit('cancel')">Cancelar</button>
        <button type="button" class="btn-primary !px-4 !py-1.5 text-sm" :disabled="busy" @click="submit">
          {{ busy ? "Enviando..." : submitLabel }}
        </button>
      </div>
    </div>
  </div>
</template>
