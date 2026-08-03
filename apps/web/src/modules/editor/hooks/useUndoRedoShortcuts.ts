import { useEffect } from 'react';

import { useHistoryStore } from '@/modules/editor/store/historyStore';

export function useUndoRedoShortcuts() {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const isMeta = event.ctrlKey || event.metaKey;
      if (!isMeta) return;

      if (event.key.toLowerCase() === 'z' && !event.shiftKey) {
        event.preventDefault();
        useHistoryStore.getState().undo();
      } else if (event.key.toLowerCase() === 'y' || (event.shiftKey && event.key.toLowerCase() === 'z')) {
        event.preventDefault();
        useHistoryStore.getState().redo();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
}
