import { describe, expect, it } from "vitest";
import { contentToHtml } from "~/utils/richText";

describe("contentToHtml", () => {
  it("convierte texto plano antiguo en párrafos escapados", () => {
    expect(contentToHtml("Hola &\nmundo\n\nOtro")).toBe(
      "<p>Hola &amp;<br>mundo</p><p>Otro</p>"
    );
  });

  it("deja intacto el HTML del editor", () => {
    expect(contentToHtml("<p>Hola <strong>x</strong></p>")).toBe("<p>Hola <strong>x</strong></p>");
  });

  it("devuelve vacío sin contenido", () => {
    expect(contentToHtml("")).toBe("");
  });
});
