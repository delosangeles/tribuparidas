export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore();
  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchMe();
  }
});
