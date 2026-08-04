import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm';
import { AuthLayout } from '@/components/layout/AuthLayout';

export default function ResetPasswordPage() {
  return (
    <AuthLayout>
      <h1 className="mb-6 text-xl font-semibold text-slate-900">Choose a new password</h1>
      <ResetPasswordForm />
    </AuthLayout>
  );
}
