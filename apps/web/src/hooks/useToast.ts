import { useUIStore } from '@/store/uiStore';

export function useToast() {
  const addNotification = useUIStore((state) => state.addNotification);

  return {
    success: (message: string) => addNotification({ id: crypto.randomUUID(), message, type: 'success' }),
    error: (message: string) => addNotification({ id: crypto.randomUUID(), message, type: 'error' }),
    info: (message: string) => addNotification({ id: crypto.randomUUID(), message, type: 'info' }),
  };
}
