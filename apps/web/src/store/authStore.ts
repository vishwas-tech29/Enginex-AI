import { create } from 'zustand';

import { authApi } from '@/services/api/auth';
import { storage } from '@/services/storage';
import { LoginPayload, RegisterPayload, TokenResponse } from '@/types/api';
import { User } from '@/types/models';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  loginWithOAuthTokens: (tokens: TokenResponse) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isAuthenticated: false,

  login: async (payload) => {
    set({ isLoading: true });
    try {
      const tokens = await authApi.login(payload);
      storage.setTokens(tokens.access_token, tokens.refresh_token, payload.rememberMe);
      set({ user: tokens.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (payload) => {
    set({ isLoading: true });
    try {
      const tokens = await authApi.register(payload);
      storage.setTokens(tokens.access_token, tokens.refresh_token);
      set({ user: tokens.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  // Tokens already arrived from the OAuth popup's callback response — no
  // API call needed, just persist and adopt them the same way login() does.
  loginWithOAuthTokens: (tokens) => {
    storage.setTokens(tokens.access_token, tokens.refresh_token);
    set({ user: tokens.user, isAuthenticated: true });
  },

  logout: () => {
    // Best-effort: the audit-log entry on the backend matters, but a user
    // must always be able to log out locally even if the request fails.
    void authApi.logout().catch(() => undefined);
    storage.clearTokens();
    set({ user: null, isAuthenticated: false });
  },

  hydrate: async () => {
    if (!storage.getAccessToken()) return;
    set({ isLoading: true });
    try {
      const user = await authApi.me();
      set({ user, isAuthenticated: true });
    } catch {
      storage.clearTokens();
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));
