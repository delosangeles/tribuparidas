<script setup lang="ts">
import jsQR from "jsqr";

// Abre la cámara (requiere HTTPS o localhost) y emite el texto del primer QR leído.
const emit = defineEmits<{ (e: "scan", value: string): void }>();

const video = ref<HTMLVideoElement | null>(null);
const error = ref("");
const active = ref(false);
let stream: MediaStream | null = null;
let frame = 0;
let detector: { detect: (source: CanvasImageSource) => Promise<{ rawValue: string }[]> } | null = null;
const work = typeof document !== "undefined" ? document.createElement("canvas") : null;

function stop() {
  cancelAnimationFrame(frame);
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
  active.value = false;
}

async function readFrame(): Promise<string | null> {
  const el = video.value;
  if (!el || el.readyState < 2) return null;
  if (detector) {
    const found = await detector.detect(el).catch(() => []);
    return found[0]?.rawValue ?? null;
  }
  if (!work) return null;
  work.width = el.videoWidth;
  work.height = el.videoHeight;
  const ctx = work.getContext("2d", { willReadFrequently: true })!;
  ctx.drawImage(el, 0, 0, work.width, work.height);
  const image = ctx.getImageData(0, 0, work.width, work.height);
  return jsQR(image.data, image.width, image.height)?.data ?? null;
}

async function loop() {
  if (!active.value) return;
  const value = await readFrame();
  if (value) {
    stop();
    emit("scan", value);
    return;
  }
  frame = requestAnimationFrame(loop);
}

async function start() {
  error.value = "";
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    error.value = "La cámara solo funciona con una conexión segura (HTTPS). Escribe el código de 6 dígitos.";
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
    const Native = (window as unknown as { BarcodeDetector?: new (o: object) => NonNullable<typeof detector> }).BarcodeDetector;
    detector = Native ? new Native({ formats: ["qr_code"] }) : null;
    active.value = true;
    await nextTick();
    if (video.value) {
      video.value.srcObject = stream;
      await video.value.play();
    }
    loop();
  } catch {
    stop();
    error.value = "No pudimos abrir la cámara. Revisa el permiso del navegador o escribe el código de 6 dígitos.";
  }
}

onBeforeUnmount(stop);
defineExpose({ start, stop });
</script>

<template>
  <div>
    <div v-if="active" class="relative overflow-hidden rounded-xl2 bg-ink">
      <video ref="video" class="aspect-square w-full object-cover" playsinline muted />
      <span class="pointer-events-none absolute inset-8 rounded-xl2 border-2 border-gold-light/80" />
    </div>
    <div class="mt-3 flex gap-2">
      <button v-if="!active" type="button" class="btn-primary" @click="start">
        <AppIcon name="camera" :size="16" /> Abrir cámara
      </button>
      <button v-else type="button" class="btn-outline" @click="stop">Cerrar cámara</button>
    </div>
    <p v-if="error" class="mt-2 text-xs text-rose-500">{{ error }}</p>
  </div>
</template>
