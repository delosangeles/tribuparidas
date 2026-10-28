/** Id del emprendimiento activo en el portal + recarga automática al cambiarlo.
 *  La primera carga va en onMounted (no durante setup) para que `load` pueda usar
 *  las variables que la página declara después de llamar a este composable. */
export function usePortalBusiness(load: (id: number) => Promise<void> | void) {
  const portal = usePortalStore();
  const businessId = computed(() => portal.currentId as number);

  onMounted(() => {
    if (businessId.value) load(businessId.value);
  });
  watch(businessId, (id) => {
    if (id) load(id);
  });

  return { portal, businessId };
}
