import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { projectsApi } from '@/services/api/projects';
import type { Project } from '@/types/models';

function ProjectDetailPageContent() {
  const router = useRouter();
  const { id } = router.query;
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id || typeof id !== 'string') return;

    void projectsApi.get(id).then(setProject).finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <p className="text-sm text-slate-500">Loading project…</p>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout>
        <p className="text-sm text-slate-500">Project not found.</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">{project.name}</h1>
            <p className="text-sm text-slate-600">{project.description || 'A focused collaboration workspace.'}</p>
          </div>
          <div className="rounded-full bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700">
            {project.type}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <p className="text-sm text-slate-500">Status</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{project.status}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Updated</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">{new Date(project.updated_at).toLocaleDateString()}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Workspace</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">Design review ready</p>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default function ProjectDetailPage() {
  return (
    <ProtectedRoute>
      <ProjectDetailPageContent />
    </ProtectedRoute>
  );
}
