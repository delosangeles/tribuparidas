import { describe, expect, it } from "vitest";
import { isPrivatePath, normalizePath } from "~/utils/routePath";

describe("normalizePath", () => {
  it("trata igual la ruta con y sin barra final (nginx agrega la barra en producción)", () => {
    expect(normalizePath("/portal/registro/")).toBe("/portal/registro");
    expect(normalizePath("/portal/registro")).toBe("/portal/registro");
    expect(normalizePath("/acceso-pendiente//")).toBe("/acceso-pendiente");
  });
  it("deja la raíz como está", () => {
    expect(normalizePath("/")).toBe("/");
  });
});

describe("isPrivatePath", () => {
  it("el registro del portal es público con y sin barra final (en producción llega con barra)", () => {
    expect(isPrivatePath("/portal/registro")).toBe(false);
    expect(isPrivatePath("/portal/registro/")).toBe(false);
  });
  it("lo privado sigue privado, con y sin barra final", () => {
    for (const path of ["/portal", "/portal/", "/portal/beneficio/", "/mi-tarjeta/", "/festejos/", "/admin/users/", "/dashboard"]) {
      expect(isPrivatePath(path), path).toBe(true);
    }
  });
  it("lo público sigue público", () => {
    for (const path of ["/", "/emprendimientos/", "/blog/mi-articulo/", "/noticias", "/login/"]) {
      expect(isPrivatePath(path), path).toBe(false);
    }
  });
});
