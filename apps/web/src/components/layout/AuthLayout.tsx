import { Sparkles } from 'lucide-react';
import { ReactNode } from 'react';

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#08040f] px-4 py-12">
      {/* Ambient glow — a CSS approximation of the flowing abstract-3D look,
          not a stock photo: three blurred, softly animated color fields
          behind the card. */}
      <div className="pointer-events-none absolute inset-0">
        <div className="animate-auth-float absolute -left-32 top-0 h-96 w-96 rounded-full bg-indigo-600/30 blur-[100px]" />
        <div
          className="animate-auth-float absolute -right-24 top-1/3 h-[28rem] w-[28rem] rounded-full bg-purple-600/25 blur-[120px]"
          style={{ animationDelay: '-1.5s' }}
        />
        <div
          className="animate-auth-float absolute bottom-0 left-1/4 h-80 w-80 rounded-full bg-violet-500/20 blur-[100px]"
          style={{ animationDelay: '-3s' }}
        />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="animate-auth-scale-in rounded-3xl border border-white/10 bg-white/[0.04] p-8 shadow-2xl shadow-purple-950/50 backdrop-blur-2xl">
          <div className="mb-6 flex flex-col items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-violet-500 shadow-lg shadow-purple-900/50">
              <Sparkles className="h-7 w-7 text-white" />
            </div>
            <span className="text-sm font-semibold uppercase tracking-[0.2em] text-white/70">Enginex AI</span>
          </div>

          {children}
        </div>
      </div>
    </div>
  );
}
