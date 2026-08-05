import { ForgotPasswordForm } from '@/components/auth/ForgotPasswordForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function ForgotPasswordPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-center text-xl font-semibold text-white">Reset your password</h1>
      <ForgotPasswordForm />
    </AuthLayout>
  );
}
