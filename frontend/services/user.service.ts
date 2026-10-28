import type { Child, Paginated, User } from "~/types";

export const userService = {
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<User>>("/admin/users/", { params });
  },
  adminSummary() {
    return useApi().get<{ all: number; active: number; pending_approval: number; unregistered: number; from_excel: number }>(
      "/admin/users/summary/"
    );
  },
  /** Aprobar = confirmar que pertenece al grupo de WhatsApp (también activa la cuenta). */
  setApproved(userId: number, isApproved: boolean) {
    return useApi().patch<User>(`/admin/users/${userId}/`, { is_approved: isApproved });
  },
  requestAccess() {
    return useApi().post<{ detail: string }>("/me/request-access/");
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
  adminUpdate(
    userId: number,
    payload: {
      first_name: string;
      last_name: string;
      whatsapp: string;
      document_id?: string | null;
      address?: string;
      department?: string;
      city?: string;
      birth_date?: string | null;
      children?: Child[];
      pregnancy?: { due_date: string } | null;
    }
  ) {
    return useApi().patch<User>(`/admin/users/${userId}/`, payload);
  },
};
