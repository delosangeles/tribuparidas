import type { User } from "~/types";

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
  register(payload: { email: string; password: string; first_name: string; last_name: string; whatsapp: string }) {
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
  updateMe(payload: { first_name: string; last_name: string }) {
    return useApi().put<User>("/me/", payload);
  },
  requestPasswordReset(email: string) {
    return useApi().post<{ detail: string }>("/auth/password-reset-request/", { email });
  },
  changePassword(payload: { current_password: string; new_password: string }) {
    return useApi().post<{ detail: string }>("/me/change-password/", payload);
  },
};
