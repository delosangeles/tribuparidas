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

// Cuenta activa pero sin aprobar (aún no se confirma que está en el grupo de WhatsApp):
// solo ve el aviso para solicitar acceso (el servidor también lo impone).
const PENDING_PATH = "/acceso-pendiente";
const needsApproval = (auth: ReturnType<typeof useAuthStore>) =>
  auth.isAuthenticated && auth.user !== null && !auth.isAdmin && auth.user.is_approved === false;

export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore();

  if (to.path === PENDING_PATH) {
    if (!authStore.isAuthenticated) return navigateTo("/login");
    if (!authStore.user) await authStore.fetchMe();
    return needsApproval(authStore) ? undefined : navigateTo("/");
  }

  if (!isPrivate(to.path)) {
    if (authStore.isAuthenticated && !authStore.user) await authStore.fetchMe();
    if (needsApproval(authStore) && to.path !== "/login") return navigateTo(PENDING_PATH);
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

  if (needsApproval(authStore)) return navigateTo(PENDING_PATH);
  if (authStore.isPortalAccount && !isPortalArea(to.path)) return navigateTo("/portal");
});
