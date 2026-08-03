import { useEffect, useState } from 'react';

import { componentsApi, Component } from '@/services/api/components';

const CATEGORIES = ['resistor', 'capacitor', 'inductor', 'diode', 'transistor', 'ic'];

interface ComponentPickerProps {
  onSelect: (component: Component) => void;
}

export function ComponentPicker({ onSelect }: ComponentPickerProps) {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('');
  const [results, setResults] = useState<Component[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!search.trim()) {
      setResults([]);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    const timer = window.setTimeout(() => {
      componentsApi
        .search(search, category || undefined)
        .then((data) => {
          if (!cancelled) setResults(data);
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [search, category]);

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <input
        type="text"
        placeholder="Search components…"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      />

      <select
        value={category}
        onChange={(event) => setCategory(event.target.value)}
        className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="">All categories</option>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {c[0]?.toUpperCase()}
            {c.slice(1)}
          </option>
        ))}
      </select>

      {isLoading && <p className="mt-3 text-sm text-slate-500">Searching…</p>}

      <div className="mt-3 space-y-2">
        {results.map((component) => (
          <button
            key={component.id}
            type="button"
            onClick={() => onSelect(component)}
            className="block w-full rounded-md border border-slate-200 p-3 text-left hover:bg-blue-50"
          >
            <div className="text-sm font-medium text-slate-900">{component.name}</div>
            <div className="text-xs text-slate-500">
              {component.part_number}
              {component.manufacturer ? ` · ${component.manufacturer}` : ''}
            </div>
          </button>
        ))}
        {!isLoading && search && results.length === 0 && (
          <p className="text-sm text-slate-500">No components found.</p>
        )}
      </div>
    </div>
  );
}
