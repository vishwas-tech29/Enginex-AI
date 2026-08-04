import { apiClient } from '@/services/api/client';
import { LoginPayload, RegisterPayload, TokenResponse } from '@/types/api';
import { User } from '@/types/models';

export type OAuthProvider = 'google' | 'github';

export const authApi = {
  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/register', payload);
    return data;
  },
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', {
      email: payload.email,
      password: payload.password,
    });
    return data;
  },
  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/api/v1/auth/me');
    return data;
  },
  async logout(): Promise<void> {
    await apiClient.post('/api/v1/auth/logout');
  },
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/api/v1/auth/password-reset', { email });
  },
  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/v1/auth/password-reset/confirm', { token, new_password: newPassword });
  },
  /** Absolute backend URL for a popup to navigate to directly — the backend
   * redirects it on to the real provider, so this never needs a fetch. */
  oauthAuthorizeUrl(provider: OAuthProvider): string {
    const baseURL = apiClient.defaults.baseURL ?? '';
    return `${baseURL}/api/v1/auth/oauth/${provider}/authorize`;
  },
};
