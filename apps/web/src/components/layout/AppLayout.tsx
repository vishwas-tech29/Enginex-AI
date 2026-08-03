import { ReactNode } from 'react';

import { Navbar } from '@/components/common/Navbar';
import { NotificationCenter } from '@/components/common/NotificationCenter';

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <Navbar />
      <NotificationCenter />
      <main>{children}</main>
    </div>
  );
}
