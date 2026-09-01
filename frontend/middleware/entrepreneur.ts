// Las secciones del dashboard de negocio (mi emprendimiento, galería,
// preguntas, estadísticas) son solo para emprendedoras. Un usuario normal
// sin negocio solo tiene acceso a /dashboard/settings.
export default defineNuxtRouteMiddleware(async () => {
  const authStore = useAuthStore();

  if (!authStore.isAuthenticated) {
    return navigateTo("/login");
  }

  if (!authStore.user) {
    await authStore.fetchMe();
  }

  if (!authStore.isEntrepreneur) {
    return navigateTo("/dashboard/settings");
  }
});
