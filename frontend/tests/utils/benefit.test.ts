import { describe, expect, it } from "vitest";
import { BENEFIT_TYPE_LABELS, suggestPortalBenefit } from "~/utils/benefit";

describe("suggestPortalBenefit", () => {
  it("toma el porcentaje del texto ya registrado y lo deja como condiciones", () => {
    expect(suggestPortalBenefit("10% de descuento para mamás de la tribu")).toEqual({
      percentage: 10,
      conditions: "10% de descuento para mamás de la tribu",
    });
    expect(suggestPortalBenefit("Hasta 25 % en kits").percentage).toBe(25);
  });
  it("sin porcentaje (o inválido) no inventa uno", () => {
    expect(suggestPortalBenefit("Envío gratis desde $80.000").percentage).toBeNull();
    expect(suggestPortalBenefit("150% de descuento").percentage).toBeNull();
    expect(suggestPortalBenefit("").conditions).toBe("");
  });
  it("tiene la etiqueta de cada tipo de beneficio", () => {
    expect(BENEFIT_TYPE_LABELS.envio_gratis).toBe("Envío gratis");
  });
});
