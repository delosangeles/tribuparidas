import { describe, expect, it } from "vitest";
import { toFormData } from "~/services/utils";

describe("toFormData", () => {
  it("omite valores null, undefined y vacíos", () => {
    const fd = toFormData({ a: "x", b: null, c: undefined, d: "" });
    expect(fd.get("a")).toBe("x");
    expect(fd.has("b")).toBe(false);
    expect(fd.has("c")).toBe(false);
    expect(fd.has("d")).toBe(false);
  });

  it("adjunta instancias de File tal cual", () => {
    const file = new File(["contenido"], "foto.png", { type: "image/png" });
    const fd = toFormData({ image: file });
    expect(fd.get("image")).toBe(file);
  });

  it("convierte números y booleanos a texto", () => {
    const fd = toFormData({ price: 4500, is_active: true });
    expect(fd.get("price")).toBe("4500");
    expect(fd.get("is_active")).toBe("true");
  });
});
