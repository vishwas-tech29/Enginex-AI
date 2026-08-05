import Link from 'next/link';

import { LoginForm } from '@/components/auth/LoginForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function LoginPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-center text-xl font-semibold text-white">Welcome back</h1>
      <LoginForm />
      <p className="mt-5 text-center text-sm text-white/50">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="font-medium text-purple-300 hover:text-purple-200">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
