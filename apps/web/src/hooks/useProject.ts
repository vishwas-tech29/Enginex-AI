import { useProjectStore } from '@/store/projectStore';

export function useProject() {
  const { projects, isLoading, fetchProjects } = useProjectStore();
  return { projects, isLoading, fetchProjects };
}
