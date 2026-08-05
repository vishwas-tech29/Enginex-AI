import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function ResetPasswordPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-center text-xl font-semibold text-white">Choose a new password</h1>
      <ResetPasswordForm />
    </AuthLayout>
  );
}
