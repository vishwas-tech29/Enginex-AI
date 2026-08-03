import Link from 'next/link';
import { useEffect } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Card } from '@/components/common/Card';
import { EmptyState } from '@/components/common/EmptyState';
import { ProjectCard } from '@/components/common/ProjectCard';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useAuth } from '@/hooks/useAuth';
import { useProject } from '@/hooks/useProject';

function DashboardContent() {
  const { user } = useAuth();
  const { projects, isLoading, fetchProjects } = useProject();

  useEffect(() => {
    void fetchProjects();
  }, [fetchProjects]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Welcome back{user?.name ? `, ${user.name}` : ''}
          </h1>
          <p className="mt-2 text-sm text-slate-600">Your design workspace is ready for the next milestone.</p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <p className="text-sm text-slate-500">Active projects</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{projects.length}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">AI assistance</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">Enabled</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Next review</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">Today</p>
          </Card>
        </div>

        {isLoading ? (
          <p className="text-sm text-slate-500">Loading projects…</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No projects yet"
            description="Create a project to start collaborating with your team."
            action={<Link href="/dashboard/projects" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white">Open projects</Link>}
          />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
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
