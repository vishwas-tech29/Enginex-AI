import { apiClient } from '@/services/api/client';

export const filesApi = {
  async upload(projectId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post(`/api/v1/files/upload?project_id=${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return data;
  },
};
