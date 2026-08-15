/** Normaliza errores de Axios/DRF a un mensaje de texto listo para mostrar al usuario. */
export function useErrorMessage(error: unknown): string {
  const err = error as { response?: { data?: Record<string, unknown> }; message?: string };
  const data = err?.response?.data;

  if (!data) return err?.message || "Ocurrió un error inesperado. Intenta de nuevo.";
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;

  const firstKey = Object.keys(data)[0];
  if (firstKey) {
    const value = data[firstKey];
    if (Array.isArray(value)) return String(value[0]);
    if (typeof value === "string") return value;
  }

  return "Ocurrió un error inesperado. Intenta de nuevo.";
}
