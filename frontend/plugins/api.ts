import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

/**
 * Instancia de Axios "cruda", sin interceptor de refresh, para no entrar en
 * bucle cuando el propio endpoint de refresh devuelve 401.
 */
declare module "#app" {
  interface NuxtApp {
    $api: AxiosInstance;
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();
  const baseURL = import.meta.server ? config.apiBaseServer : config.public.apiBase;

  const api = axios.create({ baseURL });

  let isRefreshing = false;
  let pendingQueue: Array<(token: string | null) => void> = [];

  api.interceptors.request.use((requestConfig: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore();
    if (authStore.accessToken) {
      requestConfig.headers = requestConfig.headers ?? {};
      requestConfig.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return requestConfig;
  });

  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      const authStore = useAuthStore();
      const isAuthEndpoint = String(originalRequest?.url || "").includes("/auth/");

      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint && authStore.refreshToken) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            pendingQueue.push((token) => {
              if (!token) return reject(error);
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            });
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;
        try {
          const newToken = await authStore.refreshAccessToken();
          pendingQueue.forEach((cb) => cb(newToken));
          pendingQueue = [];
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          pendingQueue.forEach((cb) => cb(null));
          pendingQueue = [];
          await authStore.logout();
          if (import.meta.client) {
            navigateTo("/login");
          }
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    }
  );

  nuxtApp.provide("api", api);
});
