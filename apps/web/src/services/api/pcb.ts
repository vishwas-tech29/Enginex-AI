import { apiClient } from '@/services/api/client';

export interface PCBBoard {
  id: string;
  file_id: string;
  name: string;
  width_mm: number;
  height_mm: number;
  layers_count: number;
  data: {
    design_rules?: Record<string, number>;
    traces?: Record<string, Trace>;
    vias?: Record<string, Via>;
  };
}

export interface PCBComponent {
  id: string;
  board_id: string;
  reference_designator: string;
  footprint_id: string | null;
  library_entry_id: string | null;
  position_x: number;
  position_y: number;
  rotation_degrees: number;
  data: Record<string, unknown>;
}

export interface XYPoint {
  x: number;
  y: number;
}

export interface Trace {
  id: string;
  layer: string;
  start: XYPoint;
  end: XYPoint;
  width: number;
  net: string;
}

export interface Via {
  id: string;
  position: XYPoint;
  pad_dia: number;
  drill_dia: number;
  from_layer: string;
  to_layer: string;
  net: string;
}

export interface DRCViolation {
  id: string;
  rule: string;
  severity: 'error' | 'warning';
  location: [number, number];
  items: string[];
  message: string;
}

export interface ERCViolation {
  id: string;
  rule: string;
  severity: 'error' | 'warning';
  net: string;
  message: string;
}

export interface PCBMesh {
  vertices: [number, number, number][];
  triangles: [number, number, number][];
  bounding_box: { min: [number, number, number]; max: [number, number, number] };
  volume: number;
  surface_area: number;
}

export const LAYERS = [
  'top_copper',
  'bottom_copper',
  'inner_copper_1',
  'inner_copper_2',
  'silkscreen_top',
  'silkscreen_bottom',
] as const;

export const pcbApi = {
  async listBoards(fileId: string): Promise<PCBBoard[]> {
    const { data } = await apiClient.get<PCBBoard[]>('/api/v1/pcb/boards', { params: { file_id: fileId } });
    return data;
  },
  async createBoard(fileId: string, name: string, widthMm: number, heightMm: number): Promise<PCBBoard> {
    const { data } = await apiClient.post<PCBBoard>('/api/v1/pcb/boards', {
      file_id: fileId, name, width_mm: widthMm, height_mm: heightMm,
    });
    return data;
  },
  async getBoard(boardId: string): Promise<PCBBoard> {
    const { data } = await apiClient.get<PCBBoard>(`/api/v1/pcb/boards/${boardId}`);
    return data;
  },

  async listComponents(boardId: string): Promise<PCBComponent[]> {
    const { data } = await apiClient.get<PCBComponent[]>('/api/v1/pcb/components', { params: { board_id: boardId } });
    return data;
  },
  async createComponent(payload: {
    boardId: string;
    referenceDesignator: string;
    footprintId?: string;
    libraryEntryId?: string;
    positionX: number;
    positionY: number;
    data?: Record<string, unknown>;
  }): Promise<PCBComponent> {
    const { data } = await apiClient.post<PCBComponent>('/api/v1/pcb/components', {
      board_id: payload.boardId,
      reference_designator: payload.referenceDesignator,
      footprint_id: payload.footprintId,
      library_entry_id: payload.libraryEntryId,
      position_x: payload.positionX,
      position_y: payload.positionY,
      data: payload.data ?? {},
    });
    return data;
  },
  async moveComponent(componentId: string, positionX: number, positionY: number): Promise<PCBComponent> {
    const { data } = await apiClient.put<PCBComponent>(`/api/v1/pcb/components/${componentId}`, {
      position_x: positionX,
      position_y: positionY,
    });
    return data;
  },
  async deleteComponent(componentId: string): Promise<void> {
    await apiClient.delete(`/api/v1/pcb/components/${componentId}`);
  },

  async addTrace(boardId: string, layer: string, start: XYPoint, end: XYPoint, net: string, width?: number) {
    const { data } = await apiClient.post<Trace>(`/api/v1/pcb/boards/${boardId}/traces`, {
      layer, start, end, net, width,
    });
    return data;
  },
  async addVia(
    boardId: string, position: XYPoint, fromLayer: string, toLayer: string, net: string,
  ) {
    const { data } = await apiClient.post<Via>(`/api/v1/pcb/boards/${boardId}/vias`, {
      position, from_layer: fromLayer, to_layer: toLayer, net,
    });
    return data;
  },
  async autoRoute(boardId: string, layer = 'top_copper') {
    const { data } = await apiClient.post<{ traces: Trace[] }>(`/api/v1/pcb/boards/${boardId}/auto-route`, {
      layer,
    });
    return data.traces;
  },
  async optimizeTraces(boardId: string, net: string) {
    const { data } = await apiClient.post<{ removed: number }>(
      `/api/v1/pcb/boards/${boardId}/optimize-traces`,
      { net },
    );
    return data.removed;
  },

  async runDRC(boardId: string): Promise<DRCViolation[]> {
    const { data } = await apiClient.post<{ violations: DRCViolation[] }>(`/api/v1/pcb/boards/${boardId}/drc`);
    return data.violations;
  },
  async runERC(boardId: string): Promise<ERCViolation[]> {
    const { data } = await apiClient.post<{ violations: ERCViolation[] }>(`/api/v1/pcb/boards/${boardId}/erc`);
    return data.violations;
  },

  async getMesh(boardId: string): Promise<PCBMesh> {
    const { data } = await apiClient.get<PCBMesh>(`/api/v1/pcb/boards/${boardId}/mesh`);
    return data;
  },

  async downloadExport(boardId: string, boardName: string, format: 'gerber' | 'drill' | 'netlist' | 'bom' | 'step') {
    // Same reasoning as cadApi.downloadExport: this needs the bearer token,
    // so a plain <a href> won't work — fetch authenticated, then trigger a
    // browser download from an in-memory blob URL.
    const response = await apiClient.get(`/api/v1/pcb/export/${format}/${boardId}`, { responseType: 'blob' });
    const extension = { gerber: 'gbr', drill: 'drl', netlist: 'net', bom: 'csv', step: 'step' }[format];
    const blobUrl = window.URL.createObjectURL(response.data as Blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${boardName}.${extension}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
