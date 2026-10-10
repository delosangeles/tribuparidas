/** Normaliza errores de Axios/DRF a un mensaje de texto listo para mostrar al usuario. */
export function useErrorMessage(error: unknown): string {
  const err = error as { response?: { data?: Record<string, unknown> }; message?: string };
  const data = err?.response?.data;

  if (!data) return err?.message || "Ocurrió un error inesperado. Intenta de nuevo.";
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;

  const firstString = (value: unknown): string | null => {
    if (typeof value === "string") return value;
    if (Array.isArray(value)) {
      for (const item of value) {
        const found = firstString(item);
        if (found) return found;
      }
    } else if (value && typeof value === "object") {
      for (const item of Object.values(value)) {
        const found = firstString(item);
        if (found) return found;
      }
    }
    return null;
  };
  const message = firstString(data);
  if (message) return message;

  return "Ocurrió un error inesperado. Intenta de nuevo.";
}
