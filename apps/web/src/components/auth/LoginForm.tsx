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
          <p className="animate-auth-slide-down text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <label className="flex flex-col gap-1 text-sm text-slate-700">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-700">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-600">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(event) => setRememberMe(event.target.checked)}
              className="rounded border-slate-300"
            />
            Remember me
          </label>
          <Link href="/forgot-password" className="font-medium text-brand-600">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" isLoading={isLoading}>
          Log in
        </Button>
      </form>
    </>
  );
}
