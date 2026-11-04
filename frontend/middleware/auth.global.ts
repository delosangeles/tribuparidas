// Sitio abierto: la portada, emprendimientos, blog, noticias y el login son
// públicos. Solo las rutas que empiezan con estos prefijos exigen sesión
// (además, cada una puede tener su propio middleware de rol: admin,
// entrepreneur, superadmin). Escribir (comentar, preguntar, opinar, crear)
// se valida en cada página y en la API.
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
  // En producción las rutas llegan con barra final ("/portal/registro/"): se comparan sin ella.
  const path = normalizePath(to.path);

  if (path === PENDING_PATH) {
    if (!authStore.isAuthenticated) return navigateTo("/login");
    if (!authStore.user) await authStore.fetchMe();
    return needsApproval(authStore) ? undefined : navigateTo("/");
  }

  if (!isPrivatePath(path)) {
    if (authStore.isAuthenticated && !authStore.user) await authStore.fetchMe();
    if (needsApproval(authStore) && path !== "/login") return navigateTo(PENDING_PATH);
    return; // las cuentas de portal ven lo público como cualquier visitante
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
  if (authStore.isPortalAccount && !isPortalArea(path)) return navigateTo("/portal");
});
