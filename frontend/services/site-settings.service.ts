export interface SiteSettings {
  /** WhatsApp (con indicativo) de quien aprueba el ingreso al grupo. */
  access_whatsapp: string;
}

export const siteSettingsService = {
  get() {
    return useApi().get<SiteSettings>("/site-settings/");
  },
  update(payload: Partial<SiteSettings>) {
    return useApi().patch<SiteSettings>("/site-settings/", payload);
  },
};
