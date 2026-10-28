export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const MAX_UPLOAD_MB = 5;
const MAX_SIDE = 1600;

/** Valida tipo y tamaño ANTES de comprimir. Devuelve el mensaje de error o null. */
export function validateImage(file: Pick<File, "type" | "size">): string | null {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) return "Formato no permitido. Usa JPG, PNG o WEBP.";
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
