import { useEffect } from 'react';

import { useLocalStorage } from '@/hooks/useLocalStorage';
import { useUIStore } from '@/store/uiStore';

export function useTheme() {
  const [theme, setThemeValue] = useLocalStorage<'light' | 'dark'>('theme', 'light');
  const setStoreTheme = useUIStore((state) => state.setTheme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    setStoreTheme(theme);
  }, [setStoreTheme, theme]);

  function setTheme(nextTheme: 'light' | 'dark') {
    setThemeValue(nextTheme);
    setStoreTheme(nextTheme);
  }

  function toggleTheme() {
    setTheme(theme === 'light' ? 'dark' : 'light');
  }

  return { theme, setTheme, toggleTheme };
}
