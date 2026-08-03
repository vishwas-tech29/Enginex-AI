import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, register, logout, hydrate } = useAuthStore();
  return { user, isAuthenticated, isLoading, login, register, logout, hydrate };
}
