import { apiClient } from '@/services/api/client';

export interface Organization {
  id: string;
  name: string;
  owner_id: string;
  subscription_tier: string;
}

export const organizationsApi = {
  async list(): Promise<Organization[]> {
    const { data } = await apiClient.get<Organization[]>('/api/v1/organizations');
    return data;
  },
  async create(name: string): Promise<Organization> {
    const { data } = await apiClient.post<Organization>('/api/v1/organizations', { name });
    return data;
  },
};
