import Link from 'next/link';

import { Card } from '@/components/common/Card';
import type { Project } from '@/types/models';

interface ProjectCardProps {
  project: Project;
}

const typeStyles: Record<Project['type'], string> = {
  cad: 'bg-blue-50 text-blue-700',
  pcb: 'bg-purple-50 text-purple-700',
  mixed: 'bg-amber-50 text-amber-700',
  robotics: 'bg-emerald-50 text-emerald-700',
};

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`} className="block">
      <Card className="h-full transition hover:-translate-y-0.5 hover:shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">{project.name}</h3>
            <p className="mt-1 text-sm text-slate-600">
              {project.description || 'No description yet'}
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${typeStyles[project.type]}`}>
            {project.type}
          </span>
        </div>
        <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
          <span>{project.status}</span>
          <span>{new Date(project.updated_at).toLocaleDateString()}</span>
        </div>
      </Card>
    </Link>
  );
}
