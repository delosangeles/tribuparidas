export default defineNuxtRouteMiddleware(async () => {
  const authStore = useAuthStore();

  if (!authStore.isAuthenticated) {
    return navigateTo("/login");
  }

  if (!authStore.user) {
    await authStore.fetchMe();
    if (!authStore.isAuthenticated) {
      return navigateTo("/login");
    }
  }
});
