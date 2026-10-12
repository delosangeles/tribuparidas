// Páginas del panel admin. Las administradoras entran a todo; una madrina solo a
// las páginas cuyo módulo (definePageMeta({ module })) tenga asignado.
const MODULE_ROUTES: [AdminModule, string][] = [
  ["usuarios", "/admin/users"],
  ["blog", "/admin/blog"],
  ["festejos", "/admin/festejos"],
];

export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore();

  if (!authStore.isAuthenticated) {
    return navigateTo("/login");
  }

  if (!authStore.user) {
    await authStore.fetchMe();
  }

  if (authStore.isAdmin) return;

  const module = to.meta.module as AdminModule | undefined;
  if (module && authStore.hasModule(module)) return;

  // Madrina sin acceso a esta página: llevarla a su primer módulo.
  const first = MODULE_ROUTES.find(([name]) => authStore.hasModule(name));
  return navigateTo(first ? first[1] : "/emprendimientos");
});
