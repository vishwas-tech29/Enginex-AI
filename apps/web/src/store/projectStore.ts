import { create } from 'zustand';

import { projectsApi } from '@/services/api/projects';
import { Project } from '@/types/models';

interface ProjectState {
  projects: Project[];
  isLoading: boolean;
  fetchProjects: () => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  isLoading: false,

  fetchProjects: async () => {
    set({ isLoading: true });
    try {
      const projects = await projectsApi.list();
      set({ projects });
    } finally {
      set({ isLoading: false });
    }
  },
}));
