import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { TokenResponse } from '../types';

const baseURL = (import.meta.env.VITE_API_URL as string | undefined) ?? '';

const apiClient = axios.create({ baseURL });

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/api/v1/auth/')
    ) {
      originalRequest._retry = true;

      const storedRefreshToken = localStorage.getItem('refresh_token');
      if (storedRefreshToken) {
        try {
          const { data } = await axios.post<TokenResponse>(`${baseURL}/api/v1/auth/refresh`, {
            refresh_token: storedRefreshToken,
          });
          setAccessToken(data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return await apiClient(originalRequest);
        } catch {
          setAccessToken(null);
          localStorage.removeItem('refresh_token');
        }
      }
    }

    return Promise.reject(error);
  },
);

export { apiClient };
