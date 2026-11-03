import type { Festejo } from "~/types";

// Imagen de felicitación (4:5, ideal para historias/estados de WhatsApp e
// Instagram) que se dibuja en el navegador con <canvas>.

const W = 1080;
const H = 1350;

const GOLD = "#C9A35A";
const GOLD_DARK = "#A8823B";
const VANILLA = "#F7F2E7";
const NUDE = "#EAD9C9";
const INK = "#3A2E1F";
const MUTED = "#8A7A66";

export interface FestejoCardText {
  greeting: string;
  name: string;
  detail: string;
  date: string;
}

/** Textos de la tarjeta según el tipo de festejo (sin fecha de nacimiento: privacidad). */
export function festejoCardText(festejo: Festejo): FestejoCardText {
  const name = festejo.child_name || festejo.mother_name;
  const [y, m, d] = festejo.event_date.split("-").map(Number);
  const date = new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" }).format(
    new Date(y, m - 1, d)
  );
  const n = festejo.number ?? 0;

  if (festejo.kind === "monthiversary") {
    return { greeting: "¡Feliz mesversario!", name, detail: `Cumple ${n} ${n === 1 ? "mes" : "meses"}`, date };
  }
  if (festejo.kind === "child_birthday" || festejo.kind === "mother_birthday") {
    return { greeting: "¡Feliz cumpleaños!", name, detail: `Cumple ${n} ${n === 1 ? "año" : "años"}`, date };
  }
  return { greeting: "¡Felicitaciones!", name: festejo.title || name, detail: festejo.note || "", date };
}

async function loadImage(url: string): Promise<HTMLImageElement | null> {
  try {
    // Se baja como blob para no "contaminar" el canvas con una imagen de otro origen.
    const response = await fetch(url, { mode: "cors" });
    if (!response.ok) return null;
    const blobUrl = URL.createObjectURL(await response.blob());
    try {
      return await new Promise<HTMLImageElement>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = blobUrl;
      });
    } finally {
      URL.revokeObjectURL(blobUrl);
    }
  } catch {
    return null;
  }
}

/** Parte un texto en líneas que quepan en `maxWidth`. */
export function wrapText(measure: (text: string) => number, text: string, maxWidth: number): string[] {
  const lines: string[] = [];
  let current = "";
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const test = current ? `${current} ${word}` : word;
    if (current && measure(test) > maxWidth) {
      lines.push(current);
      current = word;
    } else {
      current = test;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function drawCover(ctx: CanvasRenderingContext2D, img: HTMLImageElement, cx: number, cy: number, radius: number) {
  const size = radius * 2;
  const scale = Math.max(size / img.width, size / img.height);
  const w = img.width * scale;
  const h = img.height * scale;
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.clip();
  ctx.drawImage(img, cx - w / 2, cy - h / 2, w, h);
  ctx.restore();
}

export async function renderFestejoCard(festejo: Festejo, logoUrl: string): Promise<Blob> {
  try {
    await Promise.all([
      document.fonts.load('700 80px "Playfair Display"'),
      document.fonts.load('500 40px "Montserrat"'),
    ]);
  } catch {
    /* sin fuentes personalizadas se usan las de respaldo */
  }

  const canvas = document.createElement("canvas");
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext("2d")!;
  const text = festejoCardText(festejo);
  const display = '"Playfair Display", Georgia, serif';
  const sans = '"Montserrat", Arial, sans-serif';

  // Fondo
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, VANILLA);
  bg.addColorStop(1, NUDE);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // Marco dorado
  ctx.strokeStyle = GOLD;
  ctx.lineWidth = 6;
  ctx.strokeRect(40, 40, W - 80, H - 80);
  ctx.lineWidth = 2;
  ctx.strokeRect(58, 58, W - 116, H - 116);

  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";

  // Logo
  const logo = await loadImage(logoUrl);
  if (logo) {
    const lh = 120;
    const lw = (logo.width / logo.height) * lh;
    ctx.drawImage(logo, (W - lw) / 2, 100, lw, lh);
  }

  // Saludo
  ctx.fillStyle = GOLD_DARK;
  ctx.font = `700 92px ${display}`;
  ctx.fillText(text.greeting, W / 2, 330);

  // Foto grande en círculo
  const cx = W / 2;
  const cy = 710;
  const radius = 270;
  ctx.beginPath();
  ctx.arc(cx, cy, radius + 18, 0, Math.PI * 2);
  ctx.fillStyle = GOLD;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(cx, cy, radius + 6, 0, Math.PI * 2);
  ctx.fillStyle = VANILLA;
  ctx.fill();

  const photo = festejo.photo ? await loadImage(festejo.photo) : null;
  if (photo) {
    drawCover(ctx, photo, cx, cy, radius);
  } else {
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = NUDE;
    ctx.fill();
    ctx.fillStyle = GOLD;
    ctx.font = `700 260px ${display}`;
    ctx.textBaseline = "middle";
    ctx.fillText(text.name.trim().charAt(0).toUpperCase(), cx, cy + 10);
    ctx.textBaseline = "alphabetic";
  }

  // Nombre (hasta 2 líneas)
  ctx.fillStyle = INK;
  ctx.font = `700 76px ${display}`;
  const nameLines = wrapText((t) => ctx.measureText(t).width, text.name, W - 200).slice(0, 2);
  let y = 1070;
  for (const line of nameLines) {
    ctx.fillText(line, W / 2, y);
    y += 86;
  }

  if (text.detail) {
    ctx.fillStyle = GOLD_DARK;
    ctx.font = `600 46px ${sans}`;
    ctx.fillText(text.detail, W / 2, y + 8);
    y += 62;
  }

  ctx.fillStyle = MUTED;
  ctx.font = `500 34px ${sans}`;
  ctx.fillText(text.date.charAt(0).toUpperCase() + text.date.slice(1), W / 2, y + 12);

  // Pie
  ctx.fillStyle = GOLD;
  ctx.font = `600 32px ${sans}`;
  ctx.fillText("Con cariño, Tribu Paridas", W / 2, H - 90);

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("No se pudo crear la imagen."))), "image/png");
  });
}

/** Comparte la imagen (hoja de compartir del celular) o, si no se puede, la descarga. */
export async function shareFestejoCard(festejo: Festejo, logoUrl: string): Promise<"shared" | "downloaded" | "cancelled"> {
  const blob = await renderFestejoCard(festejo, logoUrl);
  const text = festejoCardText(festejo);
  const filename = `felicitacion-${text.name.toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "tribu"}.png`;
  const file = new File([blob], filename, { type: "image/png" });

  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: text.greeting, text: `${text.greeting} ${text.name} 💛` });
      return "shared";
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return "cancelled";
      // otro fallo: se descarga
    }
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return "downloaded";
}
