import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/hooks/useAuth';

function SettingsContent() {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">Settings</h1>
      <Card>
        <dl className="grid grid-cols-[120px_1fr] gap-y-3 text-sm">
          <dt className="text-slate-500">Name</dt>
          <dd className="text-slate-900">{user?.name}</dd>
          <dt className="text-slate-500">Email</dt>
          <dd className="text-slate-900">{user?.email}</dd>
        </dl>
      </Card>
    </DashboardLayout>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}
