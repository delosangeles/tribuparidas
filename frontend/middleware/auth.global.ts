// Sitio privado: por defecto TODA ruta requiere sesión. Las únicas
// excepciones son la portada (registro) y el login.
const PUBLIC_ROUTES = ["/", "/login"];

export default defineNuxtRouteMiddleware(async (to) => {
  if (PUBLIC_ROUTES.includes(to.path)) return;

  const authStore = useAuthStore();

  if (!authStore.isAuthenticated) {
    return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
  }

  if (!authStore.user) {
    await authStore.fetchMe();
    if (!authStore.isAuthenticated) {
      return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
    }
  }
});
