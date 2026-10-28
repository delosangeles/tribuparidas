import { describe, expect, it } from "vitest";
import { fitSize, isHeic, validateImage } from "~/utils/compressImage";

describe("validateImage", () => {
  it("acepta JPG, PNG y WEBP", () => {
    for (const type of ["image/jpeg", "image/png", "image/webp"]) {
      expect(validateImage({ type, size: 1000 })).toBeNull();
    }
  });

  it("acepta HEIC/HEIF de iPhone, incluso con type vacío", () => {
    expect(validateImage({ type: "image/heic", size: 1000, name: "a.heic" })).toBeNull();
    expect(validateImage({ type: "", size: 1000, name: "IMG_0001.HEIC" })).toBeNull();
  });

  it("rechaza otros formatos", () => {
    expect(validateImage({ type: "image/gif", size: 1000 })).toMatch(/Formato no permitido/);
    expect(validateImage({ type: "application/pdf", size: 1000 })).not.toBeNull();
  });

  it("rechaza archivos enormes antes de procesarlos", () => {
    expect(validateImage({ type: "image/png", size: 30 * 1024 * 1024 })).toMatch(/pesada/);
  });
});

describe("fitSize", () => {
  it("reduce el lado mayor conservando la proporción", () => {
    expect(fitSize(3200, 1600)).toEqual({ width: 1600, height: 800 });
    expect(fitSize(1000, 4000, 2000)).toEqual({ width: 500, height: 2000 });
  });

  it("no agranda imágenes pequeñas", () => {
    expect(fitSize(400, 300)).toEqual({ width: 400, height: 300 });
  });
});

describe("isHeic", () => {
  it("detecta por tipo o por extensión", () => {
    expect(isHeic({ type: "image/heif", name: "x" })).toBe(true);
    expect(isHeic({ type: "", name: "foto.HEIC" })).toBe(true);
    expect(isHeic({ type: "image/jpeg", name: "foto.jpg" })).toBe(false);
  });
});
