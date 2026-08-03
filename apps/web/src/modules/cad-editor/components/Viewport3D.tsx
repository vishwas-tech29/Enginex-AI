import { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { Grid, OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { BoxGeometry } from 'three';

export interface CADBody {
  id: string;
  name: string;
  bounds?: { width: number; height: number; depth: number };
  origin?: { x: number; y: number; z: number };
}

interface Viewport3DProps {
  bodies: CADBody[];
  height?: number;
}

/**
 * Renders CAD bodies as placeholder boxes — there's no geometry kernel yet
 * (extrude/revolve/etc. are 501 stubs, see app/api/v1/cad/service.py), so
 * this is the viewport shell the real geometry will plug into in Phase 5.
 */
export function Viewport3D({ bodies, height = 480 }: Viewport3DProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div style={{ height }} className="overflow-hidden rounded-md border border-slate-200 bg-slate-900">
      <Canvas>
        <PerspectiveCamera makeDefault position={[6, 6, 6]} fov={50} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <Grid args={[20, 20]} cellColor="#334155" sectionColor="#475569" />
        <OrbitControls makeDefault />

        {bodies.map((body) => (
          <CADBodyMesh
            key={body.id}
            body={body}
            selected={body.id === selectedId}
            onSelect={() => setSelectedId(body.id)}
          />
        ))}
      </Canvas>
    </div>
  );
}

function CADBodyMesh({
  body,
  selected,
  onSelect,
}: {
  body: CADBody;
  selected: boolean;
  onSelect: () => void;
}) {
  const bounds = body.bounds ?? { width: 1, height: 1, depth: 1 };
  const origin = body.origin ?? { x: 0, y: 0, z: 0 };
  const geometry = useMemo(
    () => new BoxGeometry(bounds.width, bounds.height, bounds.depth),
    [bounds.width, bounds.height, bounds.depth],
  );

  return (
    <group position={[origin.x, origin.y, origin.z]}>
      <mesh
        geometry={geometry}
        onClick={(event) => {
          event.stopPropagation();
          onSelect();
        }}
      >
        <meshStandardMaterial color={selected ? '#f97316' : '#2563eb'} />
      </mesh>
      <lineSegments>
        <edgesGeometry args={[geometry]} />
        <lineBasicMaterial color={selected ? '#fb923c' : '#0f172a'} />
      </lineSegments>
    </group>
  );
}
