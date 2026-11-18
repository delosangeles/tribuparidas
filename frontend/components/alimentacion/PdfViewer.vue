<script setup lang="ts">
// Visor de PDF que se ve igual en celular y en computador: dibuja cada página
// como imagen (pdf.js). Los navegadores móviles no incrustan PDF en un iframe.
const props = defineProps<{ url: string; title: string }>();

const container = ref<HTMLElement | null>(null);
const status = ref<"loading" | "ready" | "error">("loading");
const total = ref(0);
const loadedPages = ref(0);

let pdfDoc: any = null;
let observer: IntersectionObserver | null = null;
let resizeObserver: ResizeObserver | null = null;
let lastWidth = 0;
let generation = 0;

function pageBoxes(): HTMLElement[] {
  return Array.from(container.value?.querySelectorAll<HTMLElement>("[data-page]") ?? []);
}

async function renderPage(box: HTMLElement, gen: number) {
  if (!pdfDoc || box.dataset.done === String(gen)) return;
  box.dataset.done = String(gen);
  const page = await pdfDoc.getPage(Number(box.dataset.page));
  if (gen !== generation) return;
  const width = box.clientWidth || container.value!.clientWidth;
  const base = page.getViewport({ scale: 1 });
  const cssScale = width / base.width;
  const ratio = Math.min(window.devicePixelRatio || 1, 2.5);
  const viewport = page.getViewport({ scale: cssScale * ratio });
  const canvas = document.createElement("canvas");
  canvas.width = Math.floor(viewport.width);
  canvas.height = Math.floor(viewport.height);
  canvas.style.width = "100%";
  canvas.style.height = "auto";
  canvas.style.display = "block";
  await page.render({ canvasContext: canvas.getContext("2d")!, viewport }).promise;
  if (gen !== generation) return;
  box.style.minHeight = "";
  box.style.aspectRatio = `${base.width} / ${base.height}`;
  box.replaceChildren(canvas);
  loadedPages.value += 1;
}

function build() {
  generation += 1;
  loadedPages.value = 0;
  observer?.disconnect();
  const gen = generation;
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) if (entry.isIntersecting) renderPage(entry.target as HTMLElement, gen).catch(() => {});
    },
    { rootMargin: "800px 0px" }
  );
  for (const box of pageBoxes()) {
    box.dataset.done = "";
    box.replaceChildren();
    observer.observe(box);
  }
}

async function load() {
  try {
    const pdfjs = await import("pdfjs-dist");
    const worker = await import("pdfjs-dist/build/pdf.worker.min.mjs?url");
    pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
    pdfDoc = await pdfjs.getDocument({ url: props.url }).promise;
    total.value = pdfDoc.numPages;
    status.value = "ready";
    await nextTick();
    // Altura provisional de cada página con la proporción de la primera.
    const first = await pdfDoc.getPage(1);
    const v = first.getViewport({ scale: 1 });
    for (const box of pageBoxes()) box.style.aspectRatio = `${v.width} / ${v.height}`;
    lastWidth = container.value?.clientWidth ?? 0;
    build();
    resizeObserver = new ResizeObserver(() => {
      const w = container.value?.clientWidth ?? 0;
      if (Math.abs(w - lastWidth) > 40) {
        lastWidth = w;
        build();
      }
    });
    if (container.value) resizeObserver.observe(container.value);
  } catch {
    status.value = "error";
  }
}

onMounted(load);
onBeforeUnmount(() => {
  generation += 1;
  observer?.disconnect();
  resizeObserver?.disconnect();
  pdfDoc?.destroy?.();
});
</script>

<template>
  <div class="space-y-3">
    <p v-if="status === 'loading'" class="text-center text-sm text-muted">Cargando recetario…</p>
    <p v-else-if="status === 'error'" class="rounded-xl2 bg-rose-50 px-4 py-3 text-sm text-rose-600">
      No pudimos mostrar el recetario aquí. Usa «Abrir en pantalla completa» o «Descargar PDF».
    </p>
    <div v-else class="flex items-center justify-between text-xs text-muted">
      <span>{{ total }} {{ total === 1 ? "página" : "páginas" }}</span>
    </div>
    <div v-show="status === 'ready'" ref="container" class="space-y-3" :aria-label="title">
      <div
        v-for="n in total"
        :key="n"
        :data-page="n"
        class="w-full overflow-hidden rounded-xl2 border border-line bg-white shadow-soft"
        style="min-height: 200px"
      />
    </div>
  </div>
</template>
