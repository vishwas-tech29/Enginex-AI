import { useCallback, useState } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;

    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((value: T) => T)) => {
      try {
        const nextValue = value instanceof Function ? value(storedValue) : value;
        setStoredValue(nextValue);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(nextValue));
        }
      } catch {
        // Ignore storage issues in development.
      }
    },
    [key, storedValue],
  );

  return [storedValue, setValue] as const;
}
