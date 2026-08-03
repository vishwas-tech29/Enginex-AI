import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/hooks/useAuth';

function SettingsPageContent() {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Workspace settings</h1>
          <p className="text-sm text-slate-600">Manage your profile, defaults, and workspace preferences.</p>
        </div>
        <Card>
          <h2 className="text-lg font-semibold text-slate-900">Profile</h2>
          <p className="mt-2 text-sm text-slate-600">Signed in as {user?.email || 'your account'}.</p>
        </Card>
        <Card>
          <h2 className="text-lg font-semibold text-slate-900">Preferences</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-600">
            <li>Dark mode support enabled.</li>
            <li>Project templates available for CAD and PCB.</li>
            <li>AI coaching and design reviews ready.</li>
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsPageContent />
    </ProtectedRoute>
  );
}
