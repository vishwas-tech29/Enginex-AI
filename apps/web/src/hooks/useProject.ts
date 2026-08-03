import { CreateProjectPayload } from '@/services/api/projects';
import { useProjectStore } from '@/store/projectStore';

export function useProject() {
  const { projects, isLoading, fetchProjects, createProject } = useProjectStore();
  return {
    projects,
    isLoading,
    fetchProjects,
    createProject: (payload: CreateProjectPayload) => createProject(payload),
  };
}
