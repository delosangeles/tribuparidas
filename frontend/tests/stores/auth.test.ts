import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAuthStore } from "~/stores/auth";

const mockUser = {
  id: 1,
  email: "visitante@example.com",
  first_name: "Visitante",
  last_name: "Uno",
  is_staff: false,
  is_entrepreneur: false,
  created_at: "2026-01-01T00:00:00Z",
};

vi.mock("~/services/auth.service", () => ({
  authService: {
    login: vi.fn(async () => ({
      data: { access: "access-token", refresh: "refresh-token", user: mockUser },
    })),
    register: vi.fn(async () => ({
      data: { access: "access-token", refresh: "refresh-token", user: mockUser },
    })),
    logout: vi.fn(async () => ({ data: {} })),
    me: vi.fn(async () => ({ data: mockUser })),
  },
}));

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("no está autenticado por defecto", () => {
    const store = useAuthStore();
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
  });

  it("guarda tokens y usuario después de iniciar sesión", async () => {
    const store = useAuthStore();
    await store.login("visitante@example.com", "ClaveSegura123");

    expect(store.isAuthenticated).toBe(true);
    expect(store.user?.email).toBe("visitante@example.com");
  });

  it("limpia la sesión al cerrar sesión (protección de rutas)", async () => {
    const store = useAuthStore();
    await store.login("visitante@example.com", "ClaveSegura123");
    await store.logout();

    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
  });
});
