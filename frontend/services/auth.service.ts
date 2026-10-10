import type { Child, User } from "~/types";

export interface FestejosPayload {
  birth_date?: string | null;
  children?: Child[];
  pregnancy?: { due_date: string } | null;
}

/** Datos opcionales del perfil: ubicación, cédula y "Cuéntanos de ti". */
export interface ProfilePayload extends FestejosPayload {
  document_id?: string;
  address?: string;
  department?: string;
  city?: string;
  member_profile?: Record<string, string>;
  /** true = "revisé y confirmo mis datos precargados" (cierra el aviso de bienvenida). */
  confirm_data?: boolean;
}

function photoForm(file: File) {
  const form = new FormData();
  form.append("photo", file);
  return form;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export interface RegisterResponse {
  detail: string;
  user: User;
}

export const authService = {
  // No hay auto-login: la cuenta queda inactiva hasta que un admin la aprueba.
  register(
    payload: { email: string; password: string; first_name: string; last_name: string; whatsapp: string; document_id: string } & ProfilePayload
  ) {
    return useApi().post<RegisterResponse>("/auth/register/", payload);
  },
  login(email: string, password: string) {
    return useApi().post<AuthTokens>("/auth/login/", { email, password });
  },
  refresh(refresh: string) {
    return useApi().post<{ access: string; refresh?: string }>("/auth/refresh/", { refresh });
  },
  logout(refresh: string) {
    return useApi().post("/auth/logout/", { refresh });
  },
  me() {
    return useApi().get<User>("/me/");
  },
  updateMe(payload: { first_name?: string; last_name?: string } & ProfilePayload) {
    return useApi().put<User>("/me/", payload);
  },
  uploadPhoto(file: File) {
    return useApi().post<User>("/me/photo/", photoForm(file), { headers: { "Content-Type": "multipart/form-data" } });
  },
  removePhoto() {
    return useApi().delete<User>("/me/photo/");
  },
  uploadChildPhoto(childId: number, file: File) {
    return useApi().post<Child>(`/me/children/${childId}/photo/`, photoForm(file), {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  removeChildPhoto(childId: number) {
    return useApi().delete<Child>(`/me/children/${childId}/photo/`);
  },
  requestPasswordReset(email: string) {
    return useApi().post<{ detail: string }>("/auth/password-reset-request/", { email });
  },
  changePassword(payload: { current_password: string; new_password: string }) {
    return useApi().post<{ detail: string }>("/me/change-password/", payload);
  },
};
