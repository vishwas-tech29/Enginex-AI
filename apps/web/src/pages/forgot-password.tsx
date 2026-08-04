import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function ForgotPasswordPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-xl font-semibold text-slate-900">Reset your password</h1>
      <ForgotPasswordForm />
    </AuthLayout>
  );
}
