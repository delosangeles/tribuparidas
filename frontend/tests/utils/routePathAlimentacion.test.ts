import { describe, expect, it } from "vitest";
import { isPrivatePath } from "~/utils/routePath";

describe("rutas de alimentación complementaria", () => {
  it("el listado, el detalle y las guías son públicos, con y sin barra final", () => {
    for (const path of [
      "/alimentacion-complementaria",
      "/alimentacion-complementaria/",
      "/alimentacion-complementaria/pure-de-ejemplo",
      "/alimentacion-complementaria/pure-de-ejemplo/",
      "/alimentacion-complementaria/guias/senales",
    ]) {
      expect(isPrivatePath(path)).toBe(false);
    }
  });

  it("los favoritos piden sesión, con y sin barra final", () => {
    expect(isPrivatePath("/alimentacion-complementaria/favoritos")).toBe(true);
    expect(isPrivatePath("/alimentacion-complementaria/favoritos/")).toBe(true);
  });

  it("el panel admin del módulo sigue siendo privado", () => {
    expect(isPrivatePath("/admin/alimentacion")).toBe(true);
    expect(isPrivatePath("/admin/alimentacion/")).toBe(true);
  });
});
