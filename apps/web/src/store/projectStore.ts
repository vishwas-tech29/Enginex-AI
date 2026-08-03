import { create } from 'zustand';

import { CreateProjectPayload, projectsApi } from '@/services/api/projects';
import { Project } from '@/types/models';

interface ProjectState {
  projects: Project[];
  isLoading: boolean;
  fetchProjects: () => Promise<void>;
  createProject: (payload: CreateProjectPayload) => Promise<Project>;
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

  createProject: async (payload) => {
    set({ isLoading: true });
    try {
      const project = await projectsApi.create(payload);
      set((state) => ({ projects: [project, ...state.projects] }));
      return project;
    } finally {
      set({ isLoading: false });
    }
  },
}));
