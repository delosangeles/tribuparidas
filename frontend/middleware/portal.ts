// Portal de emprendimientos: requiere sesión, módulo lanzado (o equipo admin)
// y al menos un emprendimiento asignado. Las secciones de gestión (todo menos
// escanear y estadísticas) además exigen rol "dueña": `definePageMeta({ ownerOnly: true })`.
export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore();
  const flags = useFeatureFlagStore();
  const portal = usePortalStore();

  if (!authStore.isAuthenticated) {
    return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
  }
  if (!authStore.user) await authStore.fetchMe();
  if (!flags.loaded) await flags.load();

  if (!flags.isPortalLive && !authStore.isAdmin) return navigateTo("/");
  if (!authStore.hasPortalAccess) return navigateTo(authStore.isAdmin ? "/admin" : "/");

  if (!portal.loaded) {
    try {
      await portal.load();
    } catch {
      return navigateTo("/");
    }
  }
  if (to.meta.ownerOnly && !portal.isOwner) return navigateTo("/portal");
});
