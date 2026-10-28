<script setup lang="ts">
import QRCode from "qrcode";

// El QR se dibuja aquí, en el navegador; el token (firmado y con vencimiento)
// lo genera y verifica solo el servidor. No contiene datos personales.
const props = defineProps<{ value: string; size?: number }>();
const canvas = ref<HTMLCanvasElement | null>(null);

async function draw() {
  if (!canvas.value || !props.value) return;
  await QRCode.toCanvas(canvas.value, props.value, {
    width: props.size ?? 240,
    margin: 1,
    errorCorrectionLevel: "M",
    color: { dark: "#3b2f1d", light: "#ffffff" },
  });
}

onMounted(draw);
watch(() => props.value, draw);
</script>

<template>
  <canvas ref="canvas" class="rounded-xl2 bg-white" role="img" aria-label="Código QR de tu tarjeta" />
</template>
