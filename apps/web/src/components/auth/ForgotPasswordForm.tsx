import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/common/Button';
import { authApi } from '@/services/api/auth';
import { ApiError } from '@/types/errors';

export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authApi.requestPasswordReset(email);
      // The backend always returns 202 regardless of whether the email is
      // registered, so this success state doesn't confirm an account exists.
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className="animate-auth-fade-in text-center">
        <p className="text-sm text-slate-700">
          If <span className="font-medium">{email}</span> is registered, we&apos;ve sent a password reset link.
        </p>
        <Link href="/login" className="mt-4 inline-block text-sm font-medium text-brand-600">
          Back to login
        </Link>
      </div>
    );
  }

  return (
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
      <Button type="submit" isLoading={isLoading}>
        Send reset link
      </Button>
      <Link href="/login" className="text-center text-sm font-medium text-brand-600">
        Back to login
      </Link>
    </form>
  );
}
