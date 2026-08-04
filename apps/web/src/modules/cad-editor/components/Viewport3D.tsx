import { useEffect, useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { Grid, OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { BufferGeometry, DoubleSide, Float32BufferAttribute } from 'three';

import { cadApi, MeshData } from '@/services/api/cad';

interface Viewport3DProps {
  bodyId: string | null;
  height?: number;
}

/**
 * Renders a CAD body's *real* tessellated mesh (see
 * app/cad/export/exporters.py:get_mesh, backed by OCCT's own
 * triangulation) — not a placeholder cube standing in for geometry that
 * doesn't exist yet.
 */
export function Viewport3D({ bodyId, height = 480 }: Viewport3DProps) {
  const [mesh, setMesh] = useState<MeshData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!bodyId) {
      setMesh(null);
      return;
    }
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    cadApi
      .getMesh(bodyId)
      .then((data) => {
        if (!cancelled) setMesh(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load mesh');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [bodyId]);

  return (
    <div style={{ height }} className="relative overflow-hidden rounded-md border border-slate-200 bg-slate-900">
      <Canvas>
        <PerspectiveCamera makeDefault position={[30, 30, 30]} fov={50} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[50, 50, 25]} intensity={1} />
        <Grid args={[100, 100]} cellColor="#334155" sectionColor="#475569" />
        <OrbitControls makeDefault />
        {mesh && <MeshBody mesh={mesh} />}
      </Canvas>

      {!bodyId && (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400">
          No body selected yet.
        </div>
      )}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400">Loading solid…</div>
      )}
      {error && (
        <div className="absolute inset-x-0 bottom-0 bg-red-900/80 px-3 py-2 text-xs text-red-100">{error}</div>
      )}
      {mesh && (
        <div className="absolute right-3 top-3 rounded-md bg-slate-800/80 px-3 py-2 text-xs text-slate-200">
          Volume: {mesh.volume.toFixed(2)} mm³ · Surface: {mesh.surface_area.toFixed(2)} mm²
        </div>
      )}
    </div>
  );
}

function MeshBody({ mesh }: { mesh: MeshData }) {
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    const positions = new Float32Array(mesh.vertices.flat());
    const indices = mesh.triangles.flat();
    geo.setAttribute('position', new Float32BufferAttribute(positions, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }, [mesh]);

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#2563eb" side={DoubleSide} />
    </mesh>
  );
}
