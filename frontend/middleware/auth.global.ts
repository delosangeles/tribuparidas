// Sitio abierto: la portada, emprendimientos, blog, noticias y el login son
// públicos. Solo las rutas que empiezan con estos prefijos exigen sesión
// (además, cada una puede tener su propio middleware de rol: admin,
// entrepreneur, superadmin). Escribir (comentar, preguntar, opinar, crear)
// se valida en cada página y en la API.
const PRIVATE_PREFIXES = ["/dashboard", "/admin", "/festejos", "/registro", "/portal", "/mi-tarjeta"];
// El alta de cuentas del portal es pública (queda inactiva hasta que un admin la aprueba).
const PUBLIC_EXCEPTIONS = ["/portal/registro"];

function isPrivate(path: string) {
  if (PUBLIC_EXCEPTIONS.includes(path)) return false;
  return PRIVATE_PREFIXES.some((prefix) => path === prefix || path.startsWith(`${prefix}/`));
}

// Una cuenta "solo portal" únicamente usa /portal (el servidor también lo impone).
function isPortalArea(path: string) {
  return path === "/portal" || path.startsWith("/portal/") || path === "/login";
}

export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore();

  if (!isPrivate(to.path)) {
    if (authStore.isPortalAccount && !isPortalArea(to.path)) return navigateTo("/portal");
    return;
  }

  if (!authStore.isAuthenticated) {
    return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
  }

  if (!authStore.user) {
    await authStore.fetchMe();
    if (!authStore.isAuthenticated) {
      return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
    }
  }

  if (authStore.isPortalAccount && !isPortalArea(to.path)) return navigateTo("/portal");
});
