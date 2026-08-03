import Link from 'next/link';

import { LoginForm } from '@/components/auth/LoginForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function LoginPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-xl font-semibold text-slate-900">Log in to Enginex AI</h1>
      <LoginForm />
      <p className="mt-4 text-center text-sm text-slate-600">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="font-medium text-brand-600">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
