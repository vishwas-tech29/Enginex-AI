import type { AppProps } from 'next/app';
import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { NotificationCenter } from '@/components/common/NotificationCenter';
import '@/styles/globals.css';
import { useUIStore } from '@/store/uiStore';

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient());
  const theme = useUIStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      <Component {...pageProps} />
      <NotificationCenter />
    </QueryClientProvider>
  );
}
