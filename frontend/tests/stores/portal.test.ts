import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { usePortalStore } from "~/stores/portal";
import { portalService } from "~/services/portal.service";

vi.mock("~/services/portal.service", () => ({ portalService: { mine: vi.fn() } }));

const refs = [
  { business_id: 10, name: "A", slug: "a", role: "owner", logo: null },
  { business_id: 11, name: "B", slug: "b", role: "seller", logo: null },
];

describe("portal store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("selecciona el primer emprendimiento al cargar", async () => {
    vi.mocked(portalService.mine).mockResolvedValueOnce({ data: refs } as any);
    const store = usePortalStore();
    await store.load();
    expect(store.currentId).toBe(10);
    expect(store.isOwner).toBe(true);
    expect(store.loaded).toBe(true);
  });

  it("no deja seleccionar un emprendimiento ajeno", async () => {
    vi.mocked(portalService.mine).mockResolvedValueOnce({ data: refs } as any);
    const store = usePortalStore();
    await store.load();
    store.select(999);
    expect(store.currentId).toBe(10);
    store.select(11);
    expect(store.currentId).toBe(11);
    expect(store.isOwner).toBe(false); // vendedora
  });

  it("reset limpia todo (cierre de sesión)", async () => {
    vi.mocked(portalService.mine).mockResolvedValueOnce({ data: refs } as any);
    const store = usePortalStore();
    await store.load();
    store.reset();
    expect(store.businesses).toEqual([]);
    expect(store.currentId).toBeNull();
    expect(store.loaded).toBe(false);
  });
});
