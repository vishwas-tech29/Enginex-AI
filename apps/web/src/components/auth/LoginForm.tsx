import Link from 'next/link';
import { useRouter } from 'next/router';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/common/Button';
import { useAuth } from '@/hooks/useAuth';
import { ApiError } from '@/types/errors';

import { OAuthButtons } from './OAuthButtons';

export function LoginForm() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await login({ email, password, rememberMe });
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to log in');
    }
  }

  return (
    <>
      <OAuthButtons />
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <p className="animate-auth-slide-down text-sm text-red-400" role="alert">
            {error}
          </p>
        )}
        <label className="flex flex-col gap-1.5 text-sm text-white/70">
          Email address
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-white outline-none placeholder:text-white/30 focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-white/70">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-white outline-none placeholder:text-white/30 focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
          />
        </label>
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-white/60">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(event) => setRememberMe(event.target.checked)}
              className="rounded border-white/20 bg-white/5 text-purple-500 focus:ring-purple-400"
            />
            Remember me
          </label>
          <Link href="/forgot-password" className="font-medium text-purple-300 hover:text-purple-200">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" variant="authPrimary" isLoading={isLoading} className="w-full">
          Log in
        </Button>
      </form>
    </>
  );
}
