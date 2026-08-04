import { Sparkles } from 'lucide-react';
import { ReactNode } from 'react';

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="animate-auth-float mb-4 flex justify-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-600">
            <Sparkles className="h-5 w-5" />
          </div>
        </div>
        <div className="animate-auth-scale-in rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
