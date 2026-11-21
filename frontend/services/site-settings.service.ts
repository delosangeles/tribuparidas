export interface SiteSettings {
  /** WhatsApp (con indicativo) de quien aprueba el ingreso al grupo. */
  access_whatsapp: string;
  /** "1" = el lector de QR ofrece "Aplicar descuento a cliente externo". */
  external_discount_enabled: string;
}

export const siteSettingsService = {
  get() {
    return useApi().get<SiteSettings>("/site-settings/");
  },
  update(payload: Partial<SiteSettings>) {
    return useApi().patch<SiteSettings>("/site-settings/", payload);
  },
};
