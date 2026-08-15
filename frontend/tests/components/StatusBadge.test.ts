import { describe, expect, it } from "vitest";
import { mountSuspended } from "@nuxt/test-utils/runtime";
import StatusBadge from "~/components/ui/StatusBadge.vue";

describe("StatusBadge", () => {
  it("muestra la etiqueta correcta para cada estado", async () => {
    const approved = await mountSuspended(StatusBadge, { props: { status: "approved" } });
    expect(approved.text()).toContain("Aprobado");

    const pending = await mountSuspended(StatusBadge, { props: { status: "pending" } });
    expect(pending.text()).toContain("Pendiente");

    const rejected = await mountSuspended(StatusBadge, { props: { status: "rejected" } });
    expect(rejected.text()).toContain("Rechazado");
  });
});
