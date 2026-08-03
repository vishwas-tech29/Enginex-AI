import { create } from 'zustand';

interface EditorState {
  selectedObjectIds: string[];
  zoom: number;
  pan: { x: number; y: number };
  selectObjects: (ids: string[]) => void;
  deselectAll: () => void;
  setZoom: (zoom: number) => void;
  setPan: (pan: { x: number; y: number }) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  selectedObjectIds: [],
  zoom: 1,
  pan: { x: 0, y: 0 },
  selectObjects: (ids) => set({ selectedObjectIds: ids }),
  deselectAll: () => set({ selectedObjectIds: [] }),
  setZoom: (zoom) => set({ zoom }),
  setPan: (pan) => set({ pan }),
}));
