// Beneficio que un emprendimiento ya tenía registrado en su perfil (antes del portal).

export const BENEFIT_TYPE_LABELS: Record<string, string> = {
  descuento: "Descuento",
  envio_gratis: "Envío gratis",
  precio_especial: "Precio especial",
  regalo_con_compra: "Regalo con la compra",
  beneficio_exclusivo: "Beneficio exclusivo",
  otro: "Beneficio especial",
};

/** Punto de partida para el Beneficio Tribu del portal a partir del texto ya registrado.
 *  Si el texto menciona un porcentaje ("10% de descuento...") se sugiere ese valor. */
export function suggestPortalBenefit(detail: string): { percentage: number | null; conditions: string } {
  const text = (detail || "").trim();
  const match = text.match(/(\d{1,3})\s*%/);
  const percentage = match ? Number(match[1]) : null;
  return { percentage: percentage !== null && percentage >= 1 && percentage <= 100 ? percentage : null, conditions: text };
}
