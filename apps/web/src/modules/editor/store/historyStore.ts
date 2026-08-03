import { create } from 'zustand';

export interface HistoryAction {
  id: string;
  type: string;
  undo: () => void;
  redo: () => void;
}

interface HistoryState {
  past: HistoryAction[];
  future: HistoryAction[];
  push: (action: HistoryAction) => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clear: () => void;
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  past: [],
  future: [],

  push: (action) =>
    set((state) => ({
      past: [...state.past, action],
      future: [],
    })),

  undo: () => {
    const { past } = get();
    const action = past[past.length - 1];
    if (!action) return;
    action.undo();
    set((state) => ({
      past: state.past.slice(0, -1),
      future: [action, ...state.future],
    }));
  },

  redo: () => {
    const { future } = get();
    const action = future[0];
    if (!action) return;
    action.redo();
    set((state) => ({
      past: [...state.past, action],
      future: state.future.slice(1),
    }));
  },

  canUndo: () => get().past.length > 0,
  canRedo: () => get().future.length > 0,
  clear: () => set({ past: [], future: [] }),
}));
