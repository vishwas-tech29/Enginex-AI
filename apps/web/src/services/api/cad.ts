import { apiClient } from '@/services/api/client';

export interface CADObject {
  id: string;
  file_id: string;
  object_type: string;
  name: string;
  data: Record<string, unknown>;
  version_number: number;
}

export interface MeshData {
  vertices: [number, number, number][];
  triangles: [number, number, number][];
  bounding_box: { min: [number, number, number]; max: [number, number, number] };
  volume: number;
  surface_area: number;
}

export interface SolveResult {
  status: string;
  is_fully_constrained: boolean;
  residual_norm: number;
  dof_remaining: number;
  conflicting_constraints: string[];
  message: string;
}

export const cadApi = {
  async createSketch(fileId: string, name: string) {
    const { data } = await apiClient.post<CADObject>('/api/v1/cad/sketches', { file_id: fileId, name });
    return data;
  },
  async addPoint(sketchId: string, x: number, y: number, fixed = false) {
    const { data } = await apiClient.post(`/api/v1/cad/sketches/${sketchId}/points`, { x, y, fixed });
    return data as { id: string };
  },
  async addLine(sketchId: string, startId: string, endId: string) {
    const { data } = await apiClient.post(`/api/v1/cad/sketches/${sketchId}/lines`, {
      start_id: startId,
      end_id: endId,
    });
    return data as { id: string };
  },
  async addConstraint(sketchId: string, type: string, entities: string[], value?: number) {
    const { data } = await apiClient.post(`/api/v1/cad/sketches/${sketchId}/constraints`, {
      type,
      entities,
      value,
    });
    return data;
  },
  async solveSketch(sketchId: string) {
    const { data } = await apiClient.post<SolveResult>(`/api/v1/cad/sketches/${sketchId}/solve`);
    return data;
  },

  async listBodies(fileId: string) {
    const { data } = await apiClient.get<CADObject[]>('/api/v1/cad/bodies', { params: { file_id: fileId } });
    return data;
  },
  async createBody(fileId: string, name: string) {
    const { data } = await apiClient.post<CADObject>('/api/v1/cad/bodies', { file_id: fileId, name });
    return data;
  },
  async extrude(bodyId: string, sketchId: string, distance: number, symmetric = false) {
    const { data } = await apiClient.post<CADObject>(`/api/v1/cad/bodies/${bodyId}/extrude`, {
      sketch_id: sketchId,
      distance,
      symmetric,
    });
    return data;
  },
  async revolve(bodyId: string, sketchId: string, angle = 360) {
    const { data } = await apiClient.post<CADObject>(`/api/v1/cad/bodies/${bodyId}/revolve`, {
      sketch_id: sketchId,
      angle,
    });
    return data;
  },
  async fillet(bodyId: string, radius: number, selector?: string) {
    const { data } = await apiClient.post<CADObject>(`/api/v1/cad/bodies/${bodyId}/fillet`, {
      radius,
      selector,
    });
    return data;
  },
  async chamfer(bodyId: string, distance: number, selector?: string) {
    const { data } = await apiClient.post<CADObject>(`/api/v1/cad/bodies/${bodyId}/chamfer`, {
      distance,
      selector,
    });
    return data;
  },
  async getMesh(bodyId: string) {
    const { data } = await apiClient.get<MeshData>(`/api/v1/cad/bodies/${bodyId}/mesh`);
    return data;
  },
  async downloadExport(bodyId: string, bodyName: string, format: 'step' | 'stl' | 'obj') {
    // A plain <a href> to this endpoint would 401 — it needs the bearer
    // token, which only a real request (via apiClient's interceptor) sends.
    // So: fetch the bytes authenticated, then trigger the browser download
    // from an in-memory blob URL instead.
    const response = await apiClient.get(`/api/v1/cad/export/${format}/${bodyId}`, {
      responseType: 'blob',
    });
    const blobUrl = window.URL.createObjectURL(response.data as Blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${bodyName}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
