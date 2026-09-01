import type { AnalyticsSummary } from "~/types";

export const analyticsService = {
  track(path: string, sessionId: string) {
    return useApi().post("/analytics/pageview/", { path, session_id: sessionId });
  },
  summary() {
    return useApi().get<AnalyticsSummary>("/admin/analytics/summary/");
  },
};
