import { analyticsService } from "~/services/analytics.service";

// Vista de página con fines de analítica interna (solo la ve el Super Admin
// en /admin/analytics). session_id vive en sessionStorage: identifica una
// visita del navegador sin depender de sesión de servidor (la auth es JWT).
export default defineNuxtPlugin(() => {
  function getSessionId() {
    let id = sessionStorage.getItem("tp_session_id");
    if (!id) {
      id = crypto.randomUUID();
      sessionStorage.setItem("tp_session_id", id);
    }
    return id;
  }

  const sessionId = getSessionId();

  // Login, registro y el panel admin no son "contenido" de interés para la
  // analítica de visitantes (solo agregarían ruido: el equipo admin
  // navegando su propio panel, intentos de login, etc.).
  const EXCLUDED_PREFIXES = ["/login", "/registro", "/admin"];

  function track(path: string) {
    if (EXCLUDED_PREFIXES.some((prefix) => path.startsWith(prefix))) {
      return;
    }

    try {
      // Falla silenciosa: nunca debe interrumpir la navegación de la usuaria.
      analyticsService.track(path, sessionId).catch(() => {});
    } catch {
      // ignore
    }
  }

  const router = useRouter();
  track(router.currentRoute.value.fullPath);
  router.afterEach((to) => track(to.fullPath));
});
