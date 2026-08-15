/** Convierte un objeto plano en FormData, saltando valores nulos/indefinidos.
 * Necesario para endpoints que reciben archivos (logo, cover_image, imágenes). */
export function toFormData(payload: Record<string, unknown>): FormData {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    if (value instanceof File) {
      formData.append(key, value);
    } else {
      formData.append(key, String(value));
    }
  });
  return formData;
}
