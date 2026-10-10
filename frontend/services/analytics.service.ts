import type { AnalyticsSummary, MonthlyReport } from "~/types";

export const analyticsService = {
  track(path: string, sessionId: string) {
    return useApi().post("/analytics/pageview/", { path, session_id: sessionId });
  },
  monthlyReports() {
    return useApi().get<MonthlyReport[]>("/admin/reports/monthly/");
  },
  summary() {
    return useApi().get<AnalyticsSummary>("/admin/analytics/summary/");
  },
};
