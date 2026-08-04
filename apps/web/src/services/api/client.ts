import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

import { ApiError, ApiErrorBody } from '@/types/errors';
import { storage } from '@/services/storage';

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

// Concurrent 401s during the same expired-token window shouldn't each fire
// their own refresh call — they share this one in-flight promise instead.
let refreshInFlight: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = storage.getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token available');

  // A bare axios call, not `apiClient` — routing this through apiClient
  // would re-enter this same response interceptor on failure.
  const response = await axios.post<{ access_token: string; refresh_token: string }>(
    `${baseURL}/api/v1/auth/refresh`,
    { refresh_token: refreshToken },
  );
  storage.setTokens(response.data.access_token, response.data.refresh_token);
  return response.data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config as RetryableConfig | undefined;
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/');

    const canRetry =
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retried &&
      !isAuthEndpoint &&
      !!storage.getRefreshToken();

    if (canRetry) {
      originalRequest._retried = true;
      try {
        refreshInFlight ??= refreshAccessToken().finally(() => {
          refreshInFlight = null;
        });
        const newAccessToken = await refreshInFlight;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        storage.clearTokens();
      }
    } else if (error.response?.status === 401) {
      storage.clearTokens();
    }

    const message = error.response?.data?.error?.message || error.message;
    return Promise.reject(
      new ApiError(message, error.response?.status ?? 0, error.response?.data?.error?.details),
    );
  },
);
