import { ReactNode } from 'react';

import { Navbar } from '@/components/common/Navbar';

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main>{children}</main>
    </div>
  );
}
