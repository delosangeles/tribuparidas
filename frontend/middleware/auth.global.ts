// Sitio abierto: la portada, emprendimientos, blog, noticias y el login son
// públicos. Solo las rutas que empiezan con estos prefijos exigen sesión
// (además, cada una puede tener su propio middleware de rol: admin,
// entrepreneur, superadmin). Escribir (comentar, preguntar, opinar, crear)
// se valida en cada página y en la API.
const PRIVATE_PREFIXES = ["/dashboard", "/admin", "/festejos", "/registro"];

function isPrivate(path: string) {
  return PRIVATE_PREFIXES.some((prefix) => path === prefix || path.startsWith(`${prefix}/`));
}

export default defineNuxtRouteMiddleware(async (to) => {
  if (!isPrivate(to.path)) return;

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
