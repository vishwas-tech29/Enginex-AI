import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode, useEffect } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { PlanTier } from '@/types/models';

const PLAN_RANK: Record<PlanTier, number> = {
  free: 0,
  hobbyist: 1,
  professional: 2,
  enterprise: 3,
};

interface ProtectedRouteProps {
  children: ReactNode;
  /** Minimum plan tier required, e.g. "professional" — anything at or above
   * it (by PLAN_RANK) passes. Omit for routes only auth-gated, not plan-gated. */
  requiredPlan?: PlanTier;
}

export function ProtectedRoute({ children, requiredPlan }: ProtectedRouteProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, hasHydrated, hydrate } = useAuth();

  useEffect(() => {
    if (!hasHydrated) hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // Gated on hasHydrated: on a hard navigation the store resets to
    // isAuthenticated: false before hydrate()'s /auth/me call has resolved,
    // and without this the redirect fires on that stale default instead of
    // waiting for the real answer — see the hasHydrated comment in authStore.
    if (hasHydrated && !isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [hasHydrated, isLoading, isAuthenticated, router]);

  if (!hasHydrated || isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  const hasRequiredPlan = !requiredPlan || PLAN_RANK[user?.plan_tier ?? 'free'] >= PLAN_RANK[requiredPlan];

  if (!hasRequiredPlan) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
        <p className="text-lg font-semibold text-slate-900">This feature needs the {requiredPlan} plan</p>
        <p className="text-sm text-slate-600">
          You&apos;re currently on the {user?.plan_tier} plan.
        </p>
        <Link
          href="/dashboard/settings"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white"
        >
          Upgrade plan
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
