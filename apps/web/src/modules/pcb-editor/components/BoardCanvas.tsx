import { useState } from 'react';

import { DRCViolation, ERCViolation, PCBBoard, PCBComponent, XYPoint } from '@/services/api/pcb';

interface BoardCanvasProps {
  board: PCBBoard;
  components: PCBComponent[];
  mode: 'placement' | 'routing';
  activeLayer: string;
  selectedComponentId: string | null;
  onSelectComponent: (id: string) => void;
  onPlaceAt?: (position: XYPoint) => void;
  onRouteTrace?: (start: XYPoint, end: XYPoint) => void;
  violations?: (DRCViolation | ERCViolation)[];
}

const LAYER_COLORS: Record<string, string> = {
  top_copper: '#c0392b',
  bottom_copper: '#2980b9',
  inner_copper_1: '#8e44ad',
  inner_copper_2: '#16a085',
};

const PADDING_MM = 5;

export function BoardCanvas({
  board,
  components,
  mode,
  activeLayer,
  selectedComponentId,
  onSelectComponent,
  onPlaceAt,
  onRouteTrace,
  violations = [],
}: BoardCanvasProps) {
  const [pendingStart, setPendingStart] = useState<XYPoint | null>(null);

  const viewWidth = board.width_mm + PADDING_MM * 2;
  const viewHeight = board.height_mm + PADDING_MM * 2;

  function toBoardPoint(event: React.MouseEvent<SVGSVGElement>): XYPoint {
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * viewWidth - PADDING_MM;
    const y = ((event.clientY - rect.top) / rect.height) * viewHeight - PADDING_MM;
    return { x: Math.round(x * 100) / 100, y: Math.round(y * 100) / 100 };
  }

  function handleClick(event: React.MouseEvent<SVGSVGElement>) {
    const point = toBoardPoint(event);
    if (mode === 'placement') {
      onPlaceAt?.(point);
      return;
    }
    if (mode === 'routing') {
      if (!pendingStart) {
        setPendingStart(point);
      } else {
        onRouteTrace?.(pendingStart, point);
        setPendingStart(null);
      }
    }
  }

  const traces = Object.values(board.data.traces ?? {});
  const vias = Object.values(board.data.vias ?? {});
  const violationPoints = violations.filter(
    (v): v is DRCViolation => 'location' in v,
  );

  return (
    <svg
      viewBox={`${-PADDING_MM} ${-PADDING_MM} ${viewWidth} ${viewHeight}`}
      className="h-full w-full rounded-md border border-slate-200 bg-slate-950"
      onClick={handleClick}
    >
      {/* Board outline */}
      <rect x={0} y={0} width={board.width_mm} height={board.height_mm} fill="#0f3d0f" stroke="#1f6b1f" strokeWidth={0.3} />

      {/* Traces */}
      {traces
        .filter((t) => t.layer === activeLayer)
        .map((t) => (
          <line
            key={t.id}
            x1={t.start.x} y1={t.start.y} x2={t.end.x} y2={t.end.y}
            stroke={LAYER_COLORS[t.layer] ?? '#e67e22'}
            strokeWidth={t.width}
            strokeLinecap="round"
          />
        ))}

      {/* Vias */}
      {vias.map((v) => (
        <circle key={v.id} cx={v.position.x} cy={v.position.y} r={v.pad_dia / 2} fill="#f1c40f" />
      ))}

      {/* Components */}
      {components.map((c) => (
        <g
          key={c.id}
          transform={`translate(${c.position_x}, ${c.position_y}) rotate(${c.rotation_degrees})`}
          onClick={(event) => {
            event.stopPropagation();
            onSelectComponent(c.id);
          }}
          className="cursor-pointer"
        >
          <rect
            x={-1.5} y={-1} width={3} height={2}
            fill={c.id === selectedComponentId ? '#ffffff' : '#7f8c8d'}
            stroke="#ecf0f1" strokeWidth={0.1}
          />
          <text x={0} y={-1.5} fontSize={1.5} fill="#ecf0f1" textAnchor="middle">
            {c.reference_designator}
          </text>
        </g>
      ))}

      {/* DRC/ERC markers */}
      {violationPoints.map((v) => (
        <circle
          key={v.id}
          cx={v.location[0]} cy={v.location[1]} r={1.2}
          fill="none"
          stroke={v.severity === 'error' ? '#e74c3c' : '#f39c12'}
          strokeWidth={0.3}
        />
      ))}

      {pendingStart && (
        <circle cx={pendingStart.x} cy={pendingStart.y} r={0.8} fill="#3498db" />
      )}
    </svg>
  );
}
