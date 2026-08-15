export default defineNuxtConfig({
  compatibilityDate: "2024-08-01",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@pinia/nuxt"],
  css: ["~/assets/css/main.css"],

  runtimeConfig: {
    // Solo disponible en el servidor (SSR). Dentro de Docker, el backend
    // se alcanza por el nombre del servicio, no por "localhost".
    apiBaseServer: process.env.NUXT_API_BASE_SERVER || "http://backend:8000/api",
    public: {
      // Disponible en el navegador: debe ser una URL alcanzable desde fuera de Docker.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8000/api",
      siteName: process.env.NUXT_PUBLIC_SITE_NAME || "Tribu Paridas",
    },
  },

  app: {
    head: {
      title: "Tribu Paridas",
      htmlAttrs: { lang: "es" },
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        { name: "description", content: "Descubre emprendimientos hechos con pasión." },
      ],
      link: [{ rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
    },
  },

  typescript: { strict: true },

  // Evita un problema conocido de resolución del módulo virtual "#app-manifest"
  // en modo dev cuando el proyecto corre dentro de Docker con bind mounts.
  experimental: { appManifest: false },

  // Los componentes en subcarpetas (components/ui, components/business, ...)
  // se registran por su nombre de archivo, sin prefijo de carpeta.
  components: [{ path: "~/components", pathPrefix: false }],

  vite: {
    server: {
      // El watcher nativo no detecta cambios de forma confiable con bind
      // mounts de Docker en Windows; polling con intervalo moderado evita
      // tanto archivos "perdidos" como el gasto de CPU de un intervalo bajo.
      watch: { usePolling: true, interval: 1000 },
    },
  },

  devServer: {
    host: "0.0.0.0",
    port: 3000,
  },
});
