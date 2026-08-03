import Link from 'next/link';

import { Button } from '@/components/common/Button';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { useAuth } from '@/hooks/useAuth';

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between border-b border-slate-200 bg-white/90 px-6 py-4 backdrop-blur">
      <Link href="/" className="text-lg font-semibold text-slate-900">
        Enginex AI
      </Link>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        {isAuthenticated ? (
          <>
            <Link href="/dashboard" className="text-sm text-slate-600 hover:text-slate-900">
              Dashboard
            </Link>
            <span className="text-sm text-slate-600">{user?.name}</span>
            <Button variant="secondary" onClick={logout}>
              Log out
            </Button>
          </>
        ) : (
          <>
            <Link href="/login" className="text-sm text-slate-600 hover:text-slate-900">
              Log in
            </Link>
            <Link href="/register">
              <Button>Sign up</Button>
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
