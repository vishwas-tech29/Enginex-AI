import { useRouter } from 'next/router';
import { ReactNode, useEffect } from 'react';

import { useAuth } from '@/hooks/useAuth';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading, hydrate } = useAuth();

  useEffect(() => {
    hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  return <>{children}</>;
}
