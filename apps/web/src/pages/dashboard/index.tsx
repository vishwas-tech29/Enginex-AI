import { useEffect } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/hooks/useAuth';
import { useProject } from '@/hooks/useProject';

function DashboardContent() {
  const { user } = useAuth();
  const { projects, isLoading, fetchProjects } = useProject();

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <DashboardLayout>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">
        Welcome back{user?.name ? `, ${user.name}` : ''}
      </h1>
      {isLoading ? (
        <p className="text-slate-500">Loading projects…</p>
      ) : projects.length === 0 ? (
        <Card>
          <p className="text-slate-600">
            You don&apos;t have any projects yet. Create one to get started.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id}>
              <h2 className="font-medium text-slate-900">{project.name}</h2>
              <p className="text-sm text-slate-500">{project.type}</p>
            </Card>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
