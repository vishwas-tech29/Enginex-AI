import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, hasHydrated, login, register, loginWithOAuthTokens, logout, hydrate } =
    useAuthStore();
  return { user, isAuthenticated, isLoading, hasHydrated, login, register, loginWithOAuthTokens, logout, hydrate };
}
