import Link from 'next/link';

import { RegisterForm } from '@/components/auth/RegisterForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function RegisterPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-xl font-semibold text-slate-900">Create your account</h1>
      <RegisterForm />
      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-brand-600">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
