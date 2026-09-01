// Los archivos estáticos en public/ se referencian con ruta absoluta ("/logo.png"),
// pero en producción la app vive bajo un baseURL no-root ("/directorio/") — sin este
// helper, esas rutas absolutas resuelven contra la raíz del dominio y dan 404.
export function useAssetUrl(path: string) {
  const { app } = useRuntimeConfig();
  return app.baseURL.replace(/\/$/, "") + "/" + path.replace(/^\//, "");
}
