import { ReactNode } from 'react';

import { Navbar } from '@/components/common/Navbar';
import { Sidebar } from '@/components/common/Sidebar';

export function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}
