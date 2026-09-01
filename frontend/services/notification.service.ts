import type { AppNotification, Paginated } from "~/types";

export const notificationService = {
  list(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<AppNotification>>("/admin/notifications/", { params });
  },
  markRead(id: number) {
    return useApi().patch<AppNotification>(`/admin/notifications/${id}/`, { is_read: true });
  },
  markAllRead() {
    return useApi().post("/admin/notifications/mark_all_read/");
  },
};
