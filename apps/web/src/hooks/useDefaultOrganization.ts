import { useEffect, useState } from 'react';

import { organizationsApi } from '@/services/api/organizations';
import { useAuth } from '@/hooks/useAuth';

/**
 * Projects require a real organization_id. There's no multi-org UI yet, so
 * this fetches the user's first organization or provisions one named after
 * them — good enough until org management/switching lands.
 */
export function useDefaultOrganization() {
  const { user } = useAuth();
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function ensureOrganization() {
      try {
        const organizations = await organizationsApi.list();
        const first = organizations[0];
        if (first) {
          if (isMounted) setOrganizationId(first.id);
          return;
        }
        const created = await organizationsApi.create(
          user?.name ? `${user.name}'s Workspace` : 'My Workspace',
        );
        if (isMounted) setOrganizationId(created.id);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void ensureOrganization();
    return () => {
      isMounted = false;
    };
  }, [user?.name]);

  return { organizationId, isLoading };
}
