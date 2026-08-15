import type { Paginated, User } from "~/types";

export const userService = {
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<User>>("/admin/users/", { params });
  },
  setActive(userId: number, isActive: boolean) {
    return useApi().patch<User>(`/admin/users/${userId}/`, { is_active: isActive });
  },
};
