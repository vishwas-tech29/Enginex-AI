import { useEffect, useState } from 'react';

import { apiClient } from '@/services/api/client';

interface QueryOptions {
  delay?: number;
}

export function useQuery<T>(url: string, options?: QueryOptions) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;
    const timer = window.setTimeout(() => {
      void apiClient
        .get<T>(url)
        .then((response) => {
          if (isMounted) setData(response.data);
        })
        .catch((err) => {
          if (isMounted) setError(err as Error);
        })
        .finally(() => {
          if (isMounted) setIsLoading(false);
        });
    }, options?.delay ?? 0);

    return () => {
      isMounted = false;
      window.clearTimeout(timer);
    };
  }, [options?.delay, url]);

  return { data, isLoading, error };
}
