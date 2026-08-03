import { apiClient } from '@/services/api/client';

export interface Component {
  id: string;
  name: string;
  category: string;
  manufacturer: string | null;
  part_number: string;
  datasheet_url: string | null;
}

export const componentsApi = {
  async search(query: string, category?: string): Promise<Component[]> {
    const { data } = await apiClient.get<Component[]>('/api/v1/components/search', {
      params: { q: query, category },
    });
    return data;
  },
};
