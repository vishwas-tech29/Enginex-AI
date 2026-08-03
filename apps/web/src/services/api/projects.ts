import { apiClient } from '@/services/api/client';
import { Project } from '@/types/models';

export interface CreateProjectPayload {
  organization_id: string;
  team_id?: string;
  name: string;
  description?: string;
  type?: Project['type'];
}

export const projectsApi = {
  async list(): Promise<Project[]> {
    const { data } = await apiClient.get<Project[]>('/api/v1/projects');
    return data;
  },
  async get(id: string): Promise<Project> {
    const { data } = await apiClient.get<Project>(`/api/v1/projects/${id}`);
    return data;
  },
  async create(payload: CreateProjectPayload): Promise<Project> {
    const { data } = await apiClient.post<Project>('/api/v1/projects', payload);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/projects/${id}`);
  },
};
