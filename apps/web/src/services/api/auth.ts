import { apiClient } from '@/services/api/client';
import { LoginPayload, RegisterPayload, TokenResponse } from '@/types/api';
import { User } from '@/types/models';

export const authApi = {
  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/register', payload);
    return data;
  },
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload);
    return data;
  },
  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/api/v1/auth/me');
    return data;
  },
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout');
  },
};
