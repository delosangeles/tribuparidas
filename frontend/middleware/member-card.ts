// "Mi tarjeta" es para usuarias de la página, una vez lanzado el módulo (el equipo admin la ve siempre).
export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore();
  const flags = useFeatureFlagStore();

  if (!authStore.isAuthenticated) {
    return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
  }
  if (!authStore.user) await authStore.fetchMe();
  if (!flags.loaded) await flags.load();

  if (authStore.isPortalAccount) return navigateTo("/portal");
  if (!flags.isPortalLive && !authStore.isAdmin) return navigateTo("/");
});
