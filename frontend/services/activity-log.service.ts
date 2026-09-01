import type { ActivityLogEntry, Paginated } from "~/types";

export const activityLogService = {
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<ActivityLogEntry>>("/admin/activity-log/", { params });
  },
};
