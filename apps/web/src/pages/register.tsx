import Link from 'next/link';

import { RegisterForm } from '@/components/auth/RegisterForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function RegisterPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-center text-xl font-semibold text-white">Create your account</h1>
      <RegisterForm />
      <p className="mt-5 text-center text-sm text-white/50">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-purple-300 hover:text-purple-200">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
