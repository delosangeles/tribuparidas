import { describe, expect, it } from "vitest";
import { festejoCardText, wrapText } from "~/utils/festejoCard";
import type { Festejo } from "~/types";

function festejo(over: Partial<Festejo>): Festejo {
  return {
    id: 1, kind: "child_birthday", kind_label: "", event_date: "2026-11-05", user: 1, child: 1, number: 3,
    title: "", note: "", status: "approved", is_manual: false, mother_name: "Ana Pérez", child_name: "Sofía",
    headline: "", photo: null, ...over,
  };
}

describe("festejoCardText", () => {
  it("cumpleaños de hijo: saludo, nombre del niño y edad", () => {
    const t = festejoCardText(festejo({}));
    expect(t.greeting).toBe("¡Feliz cumpleaños!");
    expect(t.name).toBe("Sofía");
    expect(t.detail).toBe("Cumple 3 años");
  });
  it("cumpleaños de mamá usa el nombre de la mamá; singular en 1 año", () => {
    const t = festejoCardText(festejo({ kind: "mother_birthday", child: null, child_name: null, number: 1 }));
    expect(t.name).toBe("Ana Pérez");
    expect(t.detail).toBe("Cumple 1 año");
  });
  it("mesversario", () => {
    const t = festejoCardText(festejo({ kind: "monthiversary", number: 1 }));
    expect(t.greeting).toBe("¡Feliz mesversario!");
    expect(t.detail).toBe("Cumple 1 mes");
  });
  it("festejo manual usa el título y la nota", () => {
    const t = festejoCardText(festejo({ kind: "manual", child_name: null, title: "Graduación", note: "¡Lo logró!" }));
    expect(t).toMatchObject({ greeting: "¡Felicitaciones!", name: "Graduación", detail: "¡Lo logró!" });
  });
});

describe("wrapText", () => {
  it("parte el texto cuando no cabe", () => {
    const lines = wrapText((t) => t.length * 10, "María José del Carmen", 120);
    expect(lines).toEqual(["María José", "del Carmen"]);
  });
});
