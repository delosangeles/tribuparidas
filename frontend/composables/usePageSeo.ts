/** SEO propio de una página: title, description, canonical y Open Graph.
 *  El sitio es un SPA (sin SSR), así que las etiquetas se ponen en el navegador:
 *  los buscadores que ejecutan JS las leen; las vistas previas de WhatsApp no. */
export function usePageSeo(opts: { title: string; description?: string; path: string; image?: string | null }) {
  const config = useRuntimeConfig();
  const origin = import.meta.client ? window.location.origin : "";
  const base = config.app.baseURL.replace(/\/$/, "");
  const canonical = `${origin}${base}${opts.path}`;
  const siteName = String(config.public.siteName || "Tribu Paridas");
  const title = `${opts.title} | ${siteName}`;
  const description = (opts.description || "").replace(/\s+/g, " ").trim().slice(0, 160);

  useSeoMeta({
    title,
    description,
    ogTitle: title,
    ogDescription: description,
    ogType: "article",
    ogUrl: canonical,
    ogSiteName: siteName,
    ogImage: opts.image || undefined,
    twitterCard: opts.image ? "summary_large_image" : "summary",
  });
  useHead({ link: [{ rel: "canonical", href: canonical }] });
  return { canonical };
}
