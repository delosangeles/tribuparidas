import type { FeatureFlag, Paginated } from "~/types";

export const featureFlagService = {
  list() {
    return useApi().get<Paginated<FeatureFlag>>("/feature-flags/");
  },
  update(key: string, payload: { activate_at?: string | null; is_forced_active?: boolean }) {
    return useApi().patch<FeatureFlag>(`/feature-flags/${key}/`, payload);
  },
};
