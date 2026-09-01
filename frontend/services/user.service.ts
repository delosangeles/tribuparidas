import type { Paginated, User } from "~/types";

export const userService = {
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<User>>("/admin/users/", { params });
  },
  setActive(userId: number, isActive: boolean) {
    return useApi().patch<User>(`/admin/users/${userId}/`, { is_active: isActive });
  },
  resetPassword(userId: number) {
    return useApi().post<{ new_password: string }>(`/admin/users/${userId}/reset_password/`);
  },
  setRole(userId: number, isStaff: boolean) {
    return useApi().post<User>(`/admin/users/${userId}/set_role/`, { is_staff: isStaff });
  },
  adminCreate(payload: { email: string; first_name: string; last_name: string; whatsapp?: string; is_staff: boolean }) {
    return useApi().post<User & { new_password: string }>("/admin/users/", payload);
  },
  adminUpdate(userId: number, payload: { first_name: string; last_name: string; whatsapp: string }) {
    return useApi().patch<User>(`/admin/users/${userId}/`, payload);
  },
};
