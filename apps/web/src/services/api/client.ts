import axios, { AxiosError } from 'axios';

import { ApiError, ApiErrorBody } from '@/types/errors';
import { storage } from '@/services/storage';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.status === 401) {
      storage.clearTokens();
    }
    const message = error.response?.data?.error?.message || error.message;
    return Promise.reject(
      new ApiError(message, error.response?.status ?? 0, error.response?.data?.error?.details),
    );
  },
);
