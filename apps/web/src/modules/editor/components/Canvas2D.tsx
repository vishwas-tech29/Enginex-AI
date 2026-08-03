import { useEffect, useRef, useState } from 'react';
import { fabric } from 'fabric';

import { useHistoryStore } from '@/modules/editor/store/historyStore';
import { useUndoRedoShortcuts } from '@/modules/editor/hooks/useUndoRedoShortcuts';
import { useYjsEditor } from '@/modules/editor/hooks/useYjsEditor';

type Tool = 'select' | 'rect' | 'circle' | 'line' | 'text';

interface Canvas2DProps {
  fileId: string;
  editable?: boolean;
  height?: number;
}

const GRID_SIZE = 20;
const TOOLS: { id: Tool; label: string }[] = [
  { id: 'select', label: 'Select' },
  { id: 'rect', label: 'Rectangle' },
  { id: 'circle', label: 'Circle' },
  { id: 'line', label: 'Line' },
  { id: 'text', label: 'Text' },
];

function drawGrid(canvas: fabric.Canvas) {
  const width = canvas.getWidth();
  const height = canvas.getHeight();
  const lines: fabric.Line[] = [];

  for (let x = 0; x <= width; x += GRID_SIZE) {
    lines.push(new fabric.Line([x, 0, x, height], { stroke: '#e2e8f0', selectable: false, evented: false }));
  }
  for (let y = 0; y <= height; y += GRID_SIZE) {
    lines.push(new fabric.Line([0, y, width, y], { stroke: '#e2e8f0', selectable: false, evented: false }));
  }

  lines.forEach((line) => canvas.add(line));
  lines.forEach((line) => canvas.sendToBack(line));
}

function createShape(tool: Tool, x: number, y: number): fabric.Object | null {
  const snappedX = Math.round(x / GRID_SIZE) * GRID_SIZE;
  const snappedY = Math.round(y / GRID_SIZE) * GRID_SIZE;

  switch (tool) {
    case 'rect':
      return new fabric.Rect({
        left: snappedX,
        top: snappedY,
        width: 100,
        height: 60,
        fill: 'rgba(37, 99, 235, 0.15)',
        stroke: '#2563eb',
        strokeWidth: 2,
      });
    case 'circle':
      return new fabric.Circle({
        left: snappedX,
        top: snappedY,
        radius: 40,
        fill: 'rgba(37, 99, 235, 0.15)',
        stroke: '#2563eb',
        strokeWidth: 2,
      });
    case 'line':
      return new fabric.Line([snappedX, snappedY, snappedX + 120, snappedY], {
        stroke: '#0f172a',
        strokeWidth: 2,
      });
    case 'text':
      return new fabric.IText('Label', { left: snappedX, top: snappedY, fontSize: 16 });
    default:
      return null;
  }
}

export function Canvas2D({ fileId, editable = true, height = 480 }: Canvas2DProps) {
  const canvasElRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<fabric.Canvas | null>(null);
  const { ydoc, presence, isSynced, sendCursor } = useYjsEditor(fileId);
  const [activeTool, setActiveTool] = useState<Tool>('select');
  const pushHistory = useHistoryStore((state) => state.push);
  useUndoRedoShortcuts();

  useEffect(() => {
    if (!canvasElRef.current) return;

    const canvas = new fabric.Canvas(canvasElRef.current, {
      width: canvasElRef.current.parentElement?.clientWidth ?? 960,
      height,
      backgroundColor: '#f8fafc',
      selection: editable,
      preserveObjectStacking: true,
    });
    fabricRef.current = canvas;
    drawGrid(canvas);

    canvas.on('object:moving', (event) => {
      const target = event.target;
      if (!target) return;
      target.set({
        left: Math.round((target.left ?? 0) / GRID_SIZE) * GRID_SIZE,
        top: Math.round((target.top ?? 0) / GRID_SIZE) * GRID_SIZE,
      });
    });

    canvas.on('mouse:move', (opt) => {
      const pointer = canvas.getPointer(opt.e);
      sendCursor({ x: Math.round(pointer.x), y: Math.round(pointer.y) });
    });

    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId, height, editable]);

  // Sync canvas <-> Yjs shared map.
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    const ymap = ydoc.getMap('canvas');
    let applyingRemote = false;

    function persistLocalChange() {
      if (applyingRemote || !canvas) return;
      ymap.set('state', canvas.toJSON());
    }

    function applyRemoteState() {
      const state = ymap.get('state');
      if (!state || !canvas) return;
      applyingRemote = true;
      canvas.loadFromJSON(state, () => {
        drawGrid(canvas);
        canvas.renderAll();
        applyingRemote = false;
      });
    }

    canvas.on('object:added', persistLocalChange);
    canvas.on('object:modified', persistLocalChange);
    canvas.on('object:removed', persistLocalChange);
    ymap.observe(applyRemoteState);

    if (isSynced) applyRemoteState();

    return () => {
      canvas.off('object:added', persistLocalChange);
      canvas.off('object:modified', persistLocalChange);
      canvas.off('object:removed', persistLocalChange);
      ymap.unobserve(applyRemoteState);
    };
  }, [ydoc, isSynced]);

  // Click-to-place for the active drawing tool.
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    function handleMouseDown(opt: fabric.IEvent) {
      if (activeTool === 'select' || !canvas || opt.target) return;
      const pointer = canvas.getPointer(opt.e);
      const shape = createShape(activeTool, pointer.x, pointer.y);
      if (!shape) return;

      canvas.add(shape);
      pushHistory({
        id: `${Date.now()}-${Math.random()}`,
        type: `${activeTool}_created`,
        undo: () => {
          canvas.remove(shape);
          canvas.renderAll();
        },
        redo: () => {
          canvas.add(shape);
          canvas.renderAll();
        },
      });
      setActiveTool('select');
    }

    canvas.on('mouse:down', handleMouseDown);
    return () => {
      canvas.off('mouse:down', handleMouseDown);
    };
  }, [activeTool, pushHistory]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2 rounded-md border border-slate-200 bg-white p-2">
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            type="button"
            onClick={() => setActiveTool(tool.id)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              activeTool === tool.id ? 'bg-brand-600 text-white' : 'text-slate-700 hover:bg-slate-100'
            }`}
          >
            {tool.label}
          </button>
        ))}
        <div className="mx-2 h-5 w-px bg-slate-200" />
        <button
          type="button"
          onClick={() => useHistoryStore.getState().undo()}
          className="rounded-md px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
        >
          Undo
        </button>
        <button
          type="button"
          onClick={() => useHistoryStore.getState().redo()}
          className="rounded-md px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
        >
          Redo
        </button>
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          {isSynced ? 'Synced' : 'Connecting…'} · {presence.length} online
        </div>
      </div>

      <div className="overflow-hidden rounded-md border border-slate-200">
        <canvas ref={canvasElRef} />
      </div>

      {presence.length > 0 && (
        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
          {presence.map((p) => (
            <span key={p.user_id} className="rounded-full bg-slate-100 px-2 py-1">
              {p.name}
              {p.cursor ? ` — (${p.cursor.x}, ${p.cursor.y})` : ''}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
