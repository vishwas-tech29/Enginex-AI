import { LAYERS } from '@/services/api/pcb';

interface LayerPanelProps {
  activeLayer: string;
  onSelect: (layer: string) => void;
}

export function LayerPanel({ activeLayer, onSelect }: LayerPanelProps) {
  return (
    <div className="space-y-1">
      {LAYERS.map((layer) => (
        <button
          key={layer}
          type="button"
          onClick={() => onSelect(layer)}
          className={`block w-full rounded-md border px-2 py-1 text-left text-xs ${
            layer === activeLayer
              ? 'border-brand-600 bg-brand-50 text-brand-700'
              : 'border-slate-200 bg-white text-slate-600'
          }`}
        >
          {layer.replace(/_/g, ' ')}
        </button>
      ))}
    </div>
  );
}
