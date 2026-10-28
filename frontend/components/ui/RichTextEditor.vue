<script setup lang="ts">
import { blogService } from "~/services/blog.service";
import { compressImage, validateImage } from "~/utils/compressImage";
import { contentToHtml } from "~/utils/richText";

const props = defineProps<{
  modelValue: string;
  placeholder?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const editor = ref<HTMLElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const error = ref("");
const isEmpty = ref(!props.modelValue);

// Se guarda la selección al abrir el cuadro de archivos / enlace, porque el
// foco sale del editor y sin ella la imagen se insertaría en cualquier parte.
let savedRange: Range | null = null;

function saveSelection() {
  const selection = window.getSelection();
  if (selection?.rangeCount && editor.value?.contains(selection.anchorNode)) {
    savedRange = selection.getRangeAt(0).cloneRange();
  }
}

function restoreSelection() {
  editor.value?.focus();
  if (!savedRange) return;
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(savedRange);
}

function sync() {
  const html = editor.value?.innerHTML ?? "";
  const text = editor.value?.textContent?.trim() ?? "";
  isEmpty.value = !text && !editor.value?.querySelector("img");
  emit("update:modelValue", isEmpty.value ? "" : html);
}

function run(command: string, value?: string) {
  restoreSelection();
  document.execCommand(command, false, value);
  sync();
}

function setBlock(tag: "p" | "h2" | "h3" | "blockquote") {
  run("formatBlock", tag);
}

function addLink() {
  saveSelection();
  const url = window.prompt("Dirección del enlace (https://…)");
  if (!url?.trim()) return;
  const clean = url.trim();
  run("createLink", /^(https?:\/\/|mailto:)/i.test(clean) ? clean : `https://${clean}`);
}

function pickImage() {
  saveSelection();
  fileInput.value?.click();
}

async function handleImage(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;

  error.value = validateImage(file) ?? "";
  if (error.value) return;

  uploading.value = true;
  try {
    const compressed = await compressImage(file);
    const { data } = await blogService.uploadContentImage(compressed);
    run("insertImage", data.url);
  } catch {
    error.value = "No se pudo subir la imagen. Intenta de nuevo.";
  } finally {
    uploading.value = false;
  }
}

// Al pegar se inserta solo texto: evita arrastrar estilos y HTML de Word/web.
function handlePaste(event: ClipboardEvent) {
  event.preventDefault();
  const text = event.clipboardData?.getData("text/plain") ?? "";
  document.execCommand("insertText", false, text);
}

function isBlank() {
  return !editor.value?.textContent?.trim() && !editor.value?.querySelector("img");
}

onMounted(() => {
  if (editor.value) {
    editor.value.innerHTML = contentToHtml(props.modelValue);
    isEmpty.value = isBlank();
  }
});

// Cambios externos (ej. cargar el post a editar) sin pisar lo que se escribe.
watch(
  () => props.modelValue,
  (value) => {
    if (!editor.value) return;
    const current = isBlank() ? "" : editor.value.innerHTML;
    if (value !== current) {
      editor.value.innerHTML = contentToHtml(value);
      isEmpty.value = isBlank();
    }
  }
);

const buttons = [
  { label: "B", title: "Negrita", class: "font-bold", action: () => run("bold") },
  { label: "I", title: "Cursiva", class: "italic", action: () => run("italic") },
  { label: "U", title: "Subrayado", class: "underline", action: () => run("underline") },
  { label: "H2", title: "Título", class: "", action: () => setBlock("h2") },
  { label: "H3", title: "Subtítulo", class: "", action: () => setBlock("h3") },
  { label: "•", title: "Lista con viñetas", class: "", action: () => run("insertUnorderedList") },
  { label: "1.", title: "Lista numerada", class: "", action: () => run("insertOrderedList") },
  { label: "❝", title: "Cita", class: "", action: () => setBlock("blockquote") },
  { label: "🔗", title: "Enlace", class: "", action: addLink },
  { label: "🖼", title: "Insertar imagen", class: "", action: pickImage },
  { label: "Tx", title: "Quitar formato", class: "", action: () => { run("removeFormat"); setBlock("p"); } },
];
</script>

<template>
  <div>
    <div
      class="flex flex-wrap items-center gap-1 rounded-t-xl2 border border-b-0 border-line bg-vanilla px-2 py-1.5"
      role="toolbar"
      aria-label="Formato de texto"
    >
      <button
        v-for="button in buttons"
        :key="button.title"
        type="button"
        :title="button.title"
        :aria-label="button.title"
        class="min-w-[2rem] rounded-lg px-2 py-1 text-sm text-ink transition hover:bg-gold-light disabled:opacity-50"
        :class="button.class"
        :disabled="uploading"
        @mousedown.prevent
        @click="button.action"
      >
        {{ button.label }}
      </button>

      <span v-if="uploading" class="ml-2 text-xs text-muted">Subiendo imagen…</span>
    </div>

    <div class="relative">
      <div
        ref="editor"
        contenteditable="true"
        role="textbox"
        aria-multiline="true"
        class="rich-content field min-h-[18rem] !rounded-t-none"
        @input="sync"
        @blur="saveSelection"
        @keyup="saveSelection"
        @mouseup="saveSelection"
        @paste="handlePaste"
      />
      <p
        v-if="isEmpty"
        class="pointer-events-none absolute left-4 top-2.5 text-sm text-muted"
      >
        {{ placeholder }}
      </p>
    </div>

    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>

    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden"
      @change="handleImage"
    />
  </div>
</template>
