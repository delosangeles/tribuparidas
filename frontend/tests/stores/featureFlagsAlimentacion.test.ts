import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useFeatureFlagStore } from "~/stores/featureFlags";
import { useAuthStore } from "~/stores/auth";
import { featureFlagService } from "~/services/feature-flag.service";

vi.mock("~/services/feature-flag.service", () => ({ featureFlagService: { list: vi.fn() } }));

const flag = (active: boolean) =>
  ({
    data: {
      results: [
        { key: "alimentacion_module", label: "Alimentación", activate_at: null, is_forced_active: active, is_active: active, updated_at: "" },
      ],
    },
  }) as any;

describe("módulo alimentacion_module", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("apagado por defecto y con el flag apagado (el menú muestra «¡Próximamente!»)", async () => {
    const store = useFeatureFlagStore();
    expect(store.isAlimentacionLive).toBe(false);
    vi.mocked(featureFlagService.list).mockResolvedValueOnce(flag(false));
    await store.load();
    expect(store.isAlimentacionLive).toBe(false);
  });

  it("encendido cuando el flag está activo (desaparece el badge)", async () => {
    vi.mocked(featureFlagService.list).mockResolvedValueOnce(flag(true));
    const store = useFeatureFlagStore();
    await store.load();
    expect(store.isAlimentacionLive).toBe(true);
  });

  it("es independiente de los demás módulos", async () => {
    vi.mocked(featureFlagService.list).mockResolvedValueOnce(flag(true));
    const store = useFeatureFlagStore();
    await store.load();
    expect(store.isBlogLive).toBe(false);
    expect(store.isFestejosLive).toBe(false);
    expect(store.isPortalLive).toBe(false);
  });
});

describe("permisos de madrina sobre alimentacion", () => {
  beforeEach(() => setActivePinia(createPinia()));

  const madrina = (access: object) => {
    const auth = useAuthStore();
    auth.user = { id: 2, email: "m@example.com", is_staff: false, module_access: { alimentacion: access } } as any;
    return auth;
  };

  it("solo puede lo asignado; publicar es la acción «aprobar»", () => {
    const auth = madrina({ add: true, approve: false, edit: true, delete: false, categories: null });
    expect(auth.hasModule("alimentacion")).toBe(true);
    expect(auth.can("alimentacion", "add")).toBe(true);
    expect(auth.can("alimentacion", "approve")).toBe(false);
    expect(auth.can("alimentacion", "delete")).toBe(false);
    expect(auth.hasModule("blog")).toBe(false);
  });

  it("una usuaria común no tiene acceso y la administradora sí a todo", () => {
    const auth = useAuthStore();
    auth.user = { id: 3, email: "u@example.com", is_staff: false } as any;
    expect(auth.hasModule("alimentacion")).toBe(false);
    auth.user = { id: 1, email: "a@example.com", is_staff: true } as any;
    expect(auth.can("alimentacion", "approve")).toBe(true);
  });
});
