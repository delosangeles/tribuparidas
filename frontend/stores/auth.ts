import { defineStore } from "pinia";
import { authService } from "~/services/auth.service";
import type { User } from "~/types";

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
    } finally {
      loading.value = false;
    }
  }

  // No hay auto-login: la cuenta queda en revisión hasta que un admin la
  // aprueba (ver RegisterView en el backend). Devuelve el mensaje para que
  // la página de registro lo muestre.
  async function register(payload: { email: string; password: string; first_name: string; last_name: string; whatsapp: string }) {
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

  async function updateProfile(payload: { first_name: string; last_name: string }) {
    const { data } = await authService.updateMe(payload);
    user.value = data;
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
    login,
    register,
    fetchMe,
    refreshAccessToken,
    logout,
    updateProfile,
  };
});
