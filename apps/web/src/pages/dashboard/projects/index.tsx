import { useEffect, useState } from 'react';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { EmptyState } from '@/components/common/EmptyState';
import { ProjectCard } from '@/components/common/ProjectCard';
import { CreateProjectForm } from '@/components/forms/CreateProjectForm';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useProject } from '@/hooks/useProject';

function ProjectsPageContent() {
  const { projects, isLoading, fetchProjects } = useProject();
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    void fetchProjects();
  }, [fetchProjects]);

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Projects</h1>
            <p className="text-sm text-slate-600">Track CAD, PCB, and AI-assisted design work.</p>
          </div>
          <button
            type="button"
            onClick={() => setShowForm((value) => !value)}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white"
          >
            {showForm ? 'Hide form' : 'New project'}
          </button>
        </div>

        {showForm ? <CreateProjectForm onSuccess={() => setShowForm(false)} /> : null}

        {isLoading ? (
          <p className="text-sm text-slate-500">Loading projects…</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No projects yet"
            description="Create your first design workspace to get started."
            action={<button type="button" onClick={() => setShowForm(true)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white">Create one</button>}
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

export default function ProjectsPage() {
  return (
    <ProtectedRoute>
      <ProjectsPageContent />
    </ProtectedRoute>
  );
}
