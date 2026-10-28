export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const MAX_UPLOAD_MB = 5;
export const ACCEPT_IMAGES = "image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif";
const MAX_SIDE = 1600;

/** Las fotos de iPhone vienen en HEIC/HEIF; algunos navegadores dejan el `type` vacío. */
export function isHeic(file: Pick<File, "type" | "name">): boolean {
  return /^image\/hei[cf]$/i.test(file.type) || /\.hei[cf]$/i.test(file.name ?? "");
}

/** Convierte HEIC/HEIF a JPEG en el navegador (el servidor no los acepta). */
export async function convertHeicToJpeg(file: File): Promise<File> {
  const { default: heic2any } = await import("heic2any");
  const result = await heic2any({ blob: file, toType: "image/jpeg", quality: 0.85 });
  const blob = Array.isArray(result) ? result[0] : result;
  return new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" });
}

/** Valida tipo y tamaño ANTES de comprimir. Devuelve el mensaje de error o null. */
export function validateImage(file: Pick<File, "type" | "size"> & { name?: string }): string | null {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type) && !isHeic({ type: file.type, name: file.name ?? "" })) {
    return "Formato no permitido. Usa JPG, PNG, WEBP o HEIC.";
  }
  if (file.size > 25 * 1024 * 1024) return "La imagen es demasiado pesada para procesarla.";
  return null;
}

/** Lado mayor máximo conservando la proporción (sin agrandar). */
export function fitSize(width: number, height: number, maxSide = MAX_SIDE) {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}

/** Reduce y comprime en el navegador; el servidor vuelve a validar tipo y tamaño (≤5 MB). */
export async function compressImage(file: File, maxSide = MAX_SIDE, quality = 0.82): Promise<File> {
  const problem = validateImage(file);
  if (problem) throw new Error(problem);

  if (isHeic(file)) {
    try {
      file = await convertHeicToJpeg(file);
    } catch {
      throw new Error("No se pudo convertir la foto de iPhone (HEIC). Prueba con otra o súbela como JPG.");
    }
  }

  const bitmap = await createImageBitmap(file);
  const { width, height } = fitSize(bitmap.width, bitmap.height, maxSide);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, width, height);
  bitmap.close?.();

  const blob: Blob | null = await new Promise((resolve) => canvas.toBlob(resolve, "image/webp", quality));
  if (!blob || blob.size >= file.size) {
    // Si no mejora (o el navegador no codifica WEBP), se envía el original si cumple el límite del servidor.
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) throw new Error(`La imagen no puede superar ${MAX_UPLOAD_MB}MB.`);
    return file;
  }
  return new File([blob], file.name.replace(/\.\w+$/, "") + ".webp", { type: "image/webp" });
}
