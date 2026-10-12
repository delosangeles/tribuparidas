import { defineStore } from "pinia";
import { authService } from "~/services/auth.service";
import type { AdminAction, AdminModule, User } from "~/types";

const COOKIE_OPTS = { sameSite: "lax" as const, maxAge: 60 * 60 * 24 * 7, path: "/" };

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const accessToken = useCookie<string | null>("tp_access", COOKIE_OPTS);
  const refreshToken = useCookie<string | null>("tp_refresh", COOKIE_OPTS);
  const loading = ref(false);

  const isAuthenticated = computed(() => Boolean(accessToken.value));
  const isAdmin = computed(() => Boolean(user.value?.is_staff));
  const isSuperAdmin = computed(() => Boolean(user.value?.is_superuser));
  const isEntrepreneur = computed(() => Boolean(user.value?.is_entrepreneur));

  // Madrinas: usuarias (no administradoras) con acceso a módulos puntuales del panel.
  const moduleAccess = computed(() => user.value?.module_access ?? null);
  const isMadrina = computed(() => !isAdmin.value && Boolean(moduleAccess.value && Object.keys(moduleAccess.value).length));
  const canAccessAdmin = computed(() => isAdmin.value || isMadrina.value);

  function hasModule(module: AdminModule) {
    return isAdmin.value || Boolean(moduleAccess.value?.[module]);
  }

  /** ¿Puede hacer `action` en el módulo? En el blog se puede indicar la categoría (slug). El servidor siempre lo vuelve a validar. */
  function can(module: AdminModule, action: AdminAction, categorySlug?: string) {
    if (isAdmin.value) return true;
    const access = moduleAccess.value?.[module];
    if (!access || !access[action]) return false;
    if (module === "blog" && categorySlug && access.categories) return access.categories.includes(categorySlug);
    return true;
  }

  function setSession(tokens: { access: string; refresh: string; user: User }) {
    accessToken.value = tokens.access;
    refreshToken.value = tokens.refresh;
    user.value = tokens.user;
  }

  async function login(email: string, password: string) {
    loading.value = true;
    try {
      const { data } = await authService.login(email, password);
      setSession(data);
      // No se recarga la página tras el login, así que el plugin que carga
      // los feature flags al iniciar la app no vuelve a correr: se pide acá.
      await useFeatureFlagStore().load();
    } finally {
      loading.value = false;
    }
  }

  // No hay auto-login: la cuenta queda en revisión hasta que un admin la
  // aprueba (ver RegisterView en el backend). Devuelve el mensaje para que
  // la página de registro lo muestre.
  async function register(payload: Parameters<typeof authService.register>[0]) {
    loading.value = true;
    try {
      const { data } = await authService.register(payload);
      return data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchMe() {
    if (!accessToken.value) return;
    try {
      const { data } = await authService.me();
      user.value = data;
    } catch {
      await logout();
    }
  }

  async function refreshAccessToken(): Promise<string> {
    if (!refreshToken.value) throw new Error("No hay refresh token");
    const { data } = await authService.refresh(refreshToken.value);
    accessToken.value = data.access;
    if (data.refresh) refreshToken.value = data.refresh;
    return data.access;
  }

  async function logout() {
    const token = refreshToken.value;
    user.value = null;
    accessToken.value = null;
    refreshToken.value = null;
    if (token) {
      try {
        await authService.logout(token);
      } catch {
        // el token ya pudo haber expirado; no bloquea el logout local
      }
    }
  }

  async function updateProfile(payload: Parameters<typeof authService.updateMe>[0]) {
    const { data } = await authService.updateMe(payload);
    user.value = data;
  }

  function setUser(next: User) {
    user.value = next;
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    isEntrepreneur,
    moduleAccess,
    isMadrina,
    canAccessAdmin,
    hasModule,
    can,
    login,
    register,
    fetchMe,
    refreshAccessToken,
    logout,
    updateProfile,
    setUser,
  };
});
