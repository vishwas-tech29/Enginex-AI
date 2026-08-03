import { useState } from 'react';

import { apiClient } from '@/services/api/client';

export function useFileUpload() {
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  async function upload(file: File, projectId: string, folderId?: string) {
    setIsUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('project_id', projectId);
    if (folderId) formData.append('folder_id', folderId);
    formData.append('file', file);

    try {
      const { data } = await apiClient.post('/api/v1/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total) {
            setProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      });
      return data;
    } finally {
      setIsUploading(false);
    }
  }

  return { upload, progress, isUploading };
}
