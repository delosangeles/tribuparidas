// Antes de la fecha de lanzamiento (/admin/lanzamiento) solo entra el equipo del módulo
// (administradoras o madrinas con acceso); el resto vuelve al inicio. La API también
// responde 404 mientras el módulo esté apagado.
export default defineNuxtRouteMiddleware(async () => {
  const flags = useFeatureFlagStore();
  const authStore = useAuthStore();
  if (!flags.loaded) await flags.load();
  if (authStore.isAuthenticated && !authStore.user) await authStore.fetchMe();
  if (flags.isAlimentacionLive || authStore.hasModule("alimentacion")) return;
  return navigateTo("/");
});
