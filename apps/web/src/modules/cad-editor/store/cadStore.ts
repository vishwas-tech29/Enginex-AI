import { create } from 'zustand';

interface CADState {
  selectedIds: string[];
  setSelectedIds: (ids: string[]) => void;
}

const useCADStore = create<CADState>((set) => ({
  selectedIds: [],
  setSelectedIds: (ids) => set({ selectedIds: ids }),
}));

export default useCADStore;
