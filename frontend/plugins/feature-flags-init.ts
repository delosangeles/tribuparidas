// Los interruptores de lanzamiento (/admin/lanzamiento) se leen sin sesión:
// los visitantes también deben ver (o no) el blog según la fecha programada.
export default defineNuxtPlugin(async () => {
  await useFeatureFlagStore().load();
});
