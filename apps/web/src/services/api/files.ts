import { apiClient } from '@/services/api/client';

export interface ProjectFile {
  id: string;
  project_id: string;
  name: string;
  type: string;
  size_bytes: number;
  version_number: number;
}

export const filesApi = {
  async upload(projectId: string, file: File) {
    // project_id/folder_id are multipart form fields on the backend
    // (FastAPI `Form(...)` params), not query params — see
    // app/api/v1/files/routes.py.
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);

    const { data } = await apiClient.post('/api/v1/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return data;
  },
  async listForProject(projectId: string): Promise<ProjectFile[]> {
    const { data } = await apiClient.get<ProjectFile[]>(`/api/v1/projects/${projectId}/files`);
    return data;
  },
};
