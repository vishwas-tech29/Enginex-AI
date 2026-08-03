import { useRouter } from 'next/router';
import { useCallback } from 'react';

export function usePrefetch(url: string) {
  const router = useRouter();

  return useCallback(() => {
    void router.prefetch(url);
  }, [router, url]);
}
