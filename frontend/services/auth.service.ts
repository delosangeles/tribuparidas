import type { User } from "~/types";

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export const authService = {
  register(payload: { email: string; password: string; first_name: string; last_name: string }) {
    return useApi().post<AuthTokens>("/auth/register/", payload);
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
};
