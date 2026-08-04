import Link from 'next/link';
import { useRouter } from 'next/router';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/common/Button';
import { authApi } from '@/services/api/auth';
import { ApiError } from '@/types/errors';

export function ResetPasswordForm() {
  const router = useRouter();
  const token = typeof router.query.token === 'string' ? router.query.token : '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [succeeded, setSucceeded] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!token) {
      setError('This reset link is missing its token — request a new one.');
      return;
    }

    setIsLoading(true);
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      setSucceeded(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to reset password');
    } finally {
      setIsLoading(false);
    }
  }

  if (succeeded) {
    return (
      <div className="animate-auth-fade-in text-center">
        <p className="text-sm text-slate-700">Your password has been reset.</p>
        <Link href="/login" className="mt-4 inline-block text-sm font-medium text-brand-600">
          Log in
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
        New password
        <input
          type="password"
          required
          minLength={8}
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-slate-700">
        Confirm new password
        <input
          type="password"
          required
          minLength={8}
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2"
        />
      </label>
      <Button type="submit" isLoading={isLoading}>
        Reset password
      </Button>
    </form>
  );
}
