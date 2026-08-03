import { useEffect } from 'react';

import { useUIStore } from '@/store/uiStore';

export function NotificationCenter() {
  const notifications = useUIStore((state) => state.notifications);
  const removeNotification = useUIStore((state) => state.removeNotification);

  useEffect(() => {
    if (notifications.length === 0) return;

    const timers = notifications.map((notification) =>
      window.setTimeout(() => removeNotification(notification.id), 3200),
    );

    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [notifications, removeNotification]);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`rounded-lg border px-4 py-3 text-sm shadow-lg ${
            notification.type === 'error'
              ? 'border-red-200 bg-red-50 text-red-700'
              : notification.type === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                : 'border-slate-200 bg-white text-slate-700'
          }`}
        >
          {notification.message}
        </div>
      ))}
    </div>
  );
}
