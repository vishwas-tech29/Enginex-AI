import { useRouter } from 'next/router';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/common/Button';
import { useAuth } from '@/hooks/useAuth';
import { ApiError } from '@/types/errors';

export function LoginForm() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await login({ email, password });
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to log in');
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
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
      <Button type="submit" isLoading={isLoading}>
        Log in
      </Button>
    </form>
  );
}
