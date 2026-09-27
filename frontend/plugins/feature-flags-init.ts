export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore();
  const featureFlagStore = useFeatureFlagStore();

  if (authStore.isAuthenticated) {
    await featureFlagStore.load();
  }
});
