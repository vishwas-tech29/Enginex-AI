import { useEffect, useState } from 'react';

import { Component } from '@/services/api/components';
import {
  DRCViolation, ERCViolation, PCBBoard, PCBComponent, XYPoint, pcbApi,
} from '@/services/api/pcb';

import { BoardCanvas } from './BoardCanvas';
import { ComponentPicker } from './ComponentPicker';
import { DRCPanel } from './DRCPanel';
import { ERCPanel } from './ERCPanel';
import { LayerPanel } from './LayerPanel';

interface PCBEditorProps {
  board: PCBBoard;
  onBoardChange: (board: PCBBoard) => void;
}

export function PCBEditor({ board, onBoardChange }: PCBEditorProps) {
  const [mode, setMode] = useState<'placement' | 'routing'>('placement');
  const [activeLayer, setActiveLayer] = useState('top_copper');
  const [components, setComponents] = useState<PCBComponent[]>([]);
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(null);
  const [armedComponent, setArmedComponent] = useState<Component | null>(null);
  const [activeNet, setActiveNet] = useState('SIG1');
  const [drcViolations, setDrcViolations] = useState<DRCViolation[]>([]);
  const [ercViolations, setErcViolations] = useState<ERCViolation[]>([]);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void pcbApi.listComponents(board.id).then(setComponents);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [board.id]);

  async function refresh() {
    const [updatedBoard, updatedComponents] = await Promise.all([
      pcbApi.getBoard(board.id),
      pcbApi.listComponents(board.id),
    ]);
    onBoardChange(updatedBoard);
    setComponents(updatedComponents);
  }

  async function handlePlaceAt(position: XYPoint) {
    if (!armedComponent) {
      setError('Pick a component from the library panel first.');
      return;
    }
    setError(null);
    const prefix = armedComponent.category[0]?.toUpperCase() ?? 'U';
    const count = components.filter((c) => c.reference_designator.startsWith(prefix)).length;
    const created = await pcbApi.createComponent({
      boardId: board.id,
      referenceDesignator: `${prefix}${count + 1}`,
      libraryEntryId: armedComponent.id,
      positionX: position.x,
      positionY: position.y,
    });
    setComponents((current) => [...current, created]);
  }

  async function handleRouteTrace(start: XYPoint, end: XYPoint) {
    setError(null);
    try {
      await pcbApi.addTrace(board.id, activeLayer, start, end, activeNet);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add trace');
    }
  }

  async function handleAutoRoute() {
    setIsBusy(true);
    setError(null);
    try {
      await pcbApi.autoRoute(board.id, activeLayer);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auto-route failed');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunDRC() {
    setIsBusy(true);
    try {
      setDrcViolations(await pcbApi.runDRC(board.id));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunERC() {
    setIsBusy(true);
    try {
      setErcViolations(await pcbApi.runERC(board.id));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="flex h-[70vh] gap-4">
      {/* Left: component library */}
      <div className="w-64 shrink-0 space-y-3 overflow-y-auto">
        <ComponentPicker
          onSelect={(component) => {
            setArmedComponent(component);
            setMode('placement');
          }}
        />
        {armedComponent && (
          <p className="rounded-md bg-brand-50 p-2 text-xs text-brand-700">
            Armed: {armedComponent.name} — click the board to place it.
          </p>
        )}
      </div>

      {/* Center: board canvas */}
      <div className="flex flex-1 flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setMode('placement')}
            className={`rounded-md border px-3 py-1.5 text-sm ${mode === 'placement' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-300 bg-white text-slate-700'}`}
          >
            Place
          </button>
          <button
            type="button"
            onClick={() => setMode('routing')}
            className={`rounded-md border px-3 py-1.5 text-sm ${mode === 'routing' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-300 bg-white text-slate-700'}`}
          >
            Route
          </button>
          <input
            type="text"
            value={activeNet}
            onChange={(event) => setActiveNet(event.target.value)}
            placeholder="Net name"
            className="w-28 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          />
          <button
            type="button"
            onClick={handleAutoRoute}
            disabled={isBusy}
            className="ml-auto rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60"
          >
            Auto-route
          </button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex-1">
          <BoardCanvas
            board={board}
            components={components}
            mode={mode}
            activeLayer={activeLayer}
            selectedComponentId={selectedComponentId}
            onSelectComponent={setSelectedComponentId}
            onPlaceAt={handlePlaceAt}
            onRouteTrace={handleRouteTrace}
            violations={[...drcViolations, ...ercViolations]}
          />
        </div>
      </div>

      {/* Right: layers, DRC/ERC, export */}
      <div className="w-64 shrink-0 space-y-4 overflow-y-auto">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">Layer</h3>
          <LayerPanel activeLayer={activeLayer} onSelect={setActiveLayer} />
        </div>

        <div>
          <button
            type="button"
            onClick={handleRunDRC}
            disabled={isBusy}
            className="mb-2 w-full rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            Run DRC
          </button>
          <DRCPanel violations={drcViolations} />
        </div>

        <div>
          <button
            type="button"
            onClick={handleRunERC}
            disabled={isBusy}
            className="mb-2 w-full rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            Run ERC
          </button>
          <ERCPanel violations={ercViolations} />
        </div>

        <div className="space-y-1">
          <h3 className="text-xs font-semibold uppercase text-slate-500">Export</h3>
          {(['gerber', 'drill', 'netlist', 'bom', 'step'] as const).map((format) => (
            <button
              key={format}
              type="button"
              onClick={() => pcbApi.downloadExport(board.id, board.name, format)}
              className="block w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-left text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Export {format.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
