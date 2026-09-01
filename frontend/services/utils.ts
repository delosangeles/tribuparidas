/** Convierte un objeto plano en FormData, saltando valores nulos/indefinidos.
 *
 * `null`/`undefined` se omiten (ej. un File no seleccionado: no se debe tocar
 * la imagen ya guardada). Un string vacío "" sí se envía tal cual, porque en
 * un PATCH representa "vaciar este campo" (ej. quitarle el padre a una
 * categoría) — DRF interpreta "" como null en campos con allow_null=True. */
export function toFormData(payload: Record<string, unknown>): FormData {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value === null || value === undefined) return;
    if (value instanceof File) {
      formData.append(key, value);
    } else {
      formData.append(key, String(value));
    }
  });
  return formData;
}
